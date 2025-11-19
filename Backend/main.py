# main.py — SmartStudy AI (Cloud Run + GCS + Firestore + Gemini)
import os
import json
import re
import tempfile
import traceback
import logging
from io import BytesIO
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()  # safe: ignored in Cloud Run if .env not present

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse

# GCP
from google.cloud import storage, firestore
from google.cloud.firestore import SERVER_TIMESTAMP

# Gemini
import google.generativeai as genai

# PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -------- logging --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartstudy-ai")

# -------- config --------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # optional if using ADC
BUCKET_NAME = os.getenv("BUCKET_NAME")
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
PORT = int(os.getenv("PORT", 8080))

# Configure Gemini (api key or None -> use ADC)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Configured Gemini with API key from env.")
else:
    # If ADC is being used (e.g., Cloud Run with proper service account), leave unconfigured
    try:
        genai.configure()  # some SDKs accept no-arg to use ADC
        logger.info("Gemini configured to use ADC (no API key provided).")
    except Exception:
        logger.info("Gemini left unconfigured; ensure GEMINI_API_KEY or ADC is available.")

app = FastAPI(title="SmartStudy AI")

# -------- GCP clients (defensive) --------
storage_client = None
firestore_client = None

try:
    storage_client = storage.Client(project=PROJECT_ID) if PROJECT_ID else storage.Client()
    firestore_client = firestore.Client(project=PROJECT_ID) if PROJECT_ID else firestore.Client()
    logger.info("Initialized GCP clients.")
except Exception as e:
    logger.error("GCP client initialization failed. If running locally, set up ADC or provide service account. Error: %s", e)
    storage_client = None
    firestore_client = None

# -------- helpers --------
def extract_json(text: str):
    """
    Attempt to extract a JSON object from text and parse it.
    1) Strip code fences
    2) Find first {...} block
    3) Try json.loads, then json5, else return raw_output
    """
    if not text:
        return {"raw_output": ""}

    cleaned = text.replace("```json", "").replace("```", "").replace("`", "").strip()
    # find JSON object
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        cleaned = match.group(0)
    # try strict json
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # fallback to json5 (more forgiving)
    try:
        import json5
        return json5.loads(cleaned)
    except Exception:
        pass
    # last resort return raw trimmed text
    return {"raw_output": cleaned}



def parse_gemini_response(response):
    """
    Given the SDK response, extract combined text from candidates parts.
    Return parsed JSON if possible else raw_output structure.
    """
    try:
        if not response:
            return {"error": "no response from Gemini"}
        # handle candidates
        if not getattr(response, "candidates", None):
            return {"error": "no candidates in Gemini response"}
        candidate = response.candidates[0]
        parts = getattr(candidate.content, "parts", None)
        if not parts:
            # maybe text accessor isn't available
            return {"error": "No text returned", "finish_reason": getattr(candidate, "finish_reason", None)}
        full_text = ""
        for p in parts:
            # some parts are objects with .text
            if hasattr(p, "text"):
                full_text += p.text
            elif isinstance(p, dict) and "text" in p:
                full_text += p["text"]
            elif isinstance(p, str):
                full_text += p
        # attempt JSON extraction
        return extract_json(full_text)
    except Exception as e:
        logger.exception("Failed to parse Gemini response: %s", e)
        return {"error": "parse_failed", "traceback": traceback.format_exc()}
def convert_to_english(ai_out):
    final = []

    # Flashcards → Q/A format
    if "flashcards" in ai_out:
        for i, fc in enumerate(ai_out["flashcards"], 1):
            final.append(f"Q{i}: {fc['q']}\nA: {fc['a']}\n")

    # MCQs → Q/A format
    if "mcqs" in ai_out:
        for i, m in enumerate(ai_out["mcqs"], 1):
            final.append(f"Q{i}: {m['q']}\nAnswer: {m['answer']}\n")

    return "\n".join(final)


def call_gemini(prompt: str, model_name: str = "models/gemini-2.5-flash", max_output_tokens: int = 1500):
    """
    Call Gemini generate_content with a text prompt and return parsed JSON or raw_output.
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_output_tokens,
                "temperature": 0.3,
            }
        )
        return parse_gemini_response(response)
    except Exception as e:
        logger.exception("Gemini call failed: %s", e)
        return {"error": "gemini_call_failed", "traceback": traceback.format_exc()}

def call_gemini_with_file(file_bytes: bytes, mime_type: str, prompt: str, model_name: str = "models/gemini-2.5-flash", max_output_tokens: int = 2000):
    """
    Send a binary file + prompt to Gemini. Gemini SDK expects a list: [file_part, prompt]
    file_part: {"mime_type": "...", "data": b'...'}
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": file_bytes},
                prompt
            ],
            generation_config={"max_output_tokens": max_output_tokens, "temperature": 0.3}
        )
        return parse_gemini_response(response)
    except Exception as e:
        logger.exception("Gemini file call failed: %s", e)
        return {"error": "gemini_file_call_failed", "traceback": traceback.format_exc()}

def save_to_firestore(user_id: str, title: str, data: dict):
    if firestore_client is None:
        raise RuntimeError("Firestore client not initialized. Ensure ADC or service account is configured.")
    doc_ref = firestore_client.collection("users").document(user_id).collection("notes").document()
    payload = {
        "title": title,
        "result": data,
        "created_at": SERVER_TIMESTAMP
    }
    doc_ref.set(payload)
    return doc_ref.id

def upload_to_gcs(local_path: str, dest_blob_name: str):
    if storage_client is None:
        raise RuntimeError("Storage client not initialized. Ensure ADC or service account is configured.")
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(dest_blob_name)
    blob.upload_from_filename(local_path)
    # Return standard storage URL (works if bucket is public or you handle IAM)
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{dest_blob_name}"



# -------- routes --------
@app.get("/", response_class=HTMLResponse)
def home():
    """Serve frontend.html (make sure it's present)"""
    try:
        with open("frontend.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse("<h3>SmartStudy AI</h3><p>Frontend not found. Upload frontend.html to project root.</p>", status_code=200)

@app.post("/process-text")
async def process_text(user_id: str = Form(...), title: str = Form(...), text: str = Form(...)):
    prompt = (
        "Generate structured study material in STRICT JSON:\n"
        "{\n"
        "  \"summary\": \"...\"\n"
        "}\n\n"
        "Text to summarize:\n"
        + text
    )
    ai = call_gemini(prompt)
    doc_id = save_to_firestore(user_id, title, ai)
    return {"status": "ok", "doc_id": doc_id, "result": ai}

@app.post("/upload-file")
async def upload_file(user_id: str = Form(...), title: str = Form(...), file: UploadFile = File(...)):
    try:
        # Read file bytes
        file_bytes = await file.read()

        # Detect MIME type properly
        mime_type = file.content_type or "application/octet-stream"

        # ---------- PROMPT ----------
        prompt = """
        You are an AI study assistant. Extract readable text from the uploaded file.
        Then generate structured study material in strictly valid JSON:
        {
            "summary": "..."
        }
        Return ONLY JSON. No explanation text.
        """

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": file_bytes},
                prompt
            ],
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2000
            }
        )

        # ---------- GET RAW TEXT ----------
        if not response.candidates:
            return {"error": "No candidates returned from Gemini"}

        full_text = ""
        parts = response.candidates[0].content.parts
        for p in parts:
            if hasattr(p, "text"):
                full_text += p.text

        # ---------- EXTRACT JSON ----------
        raw = extract_json(full_text)

        # If backend output is { "raw_output": "{...json...}" }
        if isinstance(raw, dict) and "raw_output" in raw:
            try:
                result = json.loads(raw["raw_output"])
            except:
                result = raw
        else:
            result = raw

        # ---------- SAVE ----------
        doc_id = save_to_firestore(user_id, title, result)

        return {
            "status": "ok",
            "doc_id": doc_id,
            "result": result
        }

    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/generate-mcq-flashcards")
async def generate_mcq_flashcards(
    user_id: str = Form(...),
    source_text: str = Form(None),
    doc_id: str = Form(None),
    title: str = Form("MCQ & Flashcards")
):
    """
    Generate MCQs and flashcards from provided text or existing saved doc_id (Firestore).
    """
    try:
        if not (source_text or doc_id):
            return JSONResponse({"error": "Provide source_text or doc_id"}, status_code=400)

        text = ""
        if doc_id:
            if firestore_client is None:
                return JSONResponse({"error": "Firestore not initialized"}, status_code=500)

            doc_ref = firestore_client.collection("users").document(user_id)\
                                      .collection("notes").document(doc_id)
            doc = doc_ref.get()

            if not doc.exists:
                return JSONResponse({"error": "doc_id not found"}, status_code=404)

            stored = doc.to_dict().get("result", {})
            text = stored.get("summary") or stored.get("raw_output") or json.dumps(stored)
        else:
            text = source_text

        # ---------- SAFE PROMPT ----------
        prompt = (
            "Your task is to return ONE single JSON object with EXACTLY the following keys:\n\n"
            "{\n"
            "  \"flashcards\": [\n"
            "    {\"q\": \"\", \"a\": \"\"},\n"
            "    {\"q\": \"\", \"a\": \"\"},\n"
            "    {\"q\": \"\", \"a\": \"\"},\n"
            "    {\"q\": \"\", \"a\": \"\"},\n"
            "    {\"q\": \"\", \"a\": \"\"}\n"
            "  ],\n"
            "}\n\n"
            "Rules:\n"
            "- Return ONLY JSON.\n"
            "- No markdown.\n"
            "- No extra text.\n"
            "- No explanations.\n"
            "- All questions must be based STRICTLY on the provided text.\n\n"
            "Text:\n" + text
        )

        ai_out = call_gemini(prompt, max_output_tokens=1200)

        # ---- SAVE ----
        try:
            saved_id = save_to_firestore(user_id, title, ai_out)
        except Exception as e:
            logger.warning("Could not save MCQ/flashcards to Firestore: %s", e)
            saved_id = None
        if isinstance(ai_out, dict) and "raw_output" in ai_out:
            try:
                ai_out = json.loads(ai_out["raw_output"])
            except:
                pass
        english_output = convert_to_english(ai_out)

        return JSONResponse({
            "status": "ok",
            "doc_id": saved_id,
            "result": convert_to_english(ai_out)  # MUST BE formatted English
            })


    except Exception as e:
        logger.exception("generate-mcq-flashcards failed")
        return JSONResponse(
            {"error": str(e), "traceback": traceback.format_exc()},
            status_code=500
        )


@app.get("/list-models")
def list_models():
    try:
        return genai.list_models()
    except Exception as e:
        logger.exception("list-models failed")
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=500)

# Run local dev
if __name__ == "__main__":
    logger.info(f"Starting SmartStudy AI on 0.0.0.0:{PORT}")
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
