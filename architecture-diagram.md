# SmartStudy AI – Architecture Overview

This architecture features a scalable, serverless, AI-driven application deployed on Google Cloud Run.

## 1. Application Layer (Frontend)
- Static HTML/CSS/JS frontend
- Light/Dark mode toggle
- REST API Client
- File upload, summary generation UI
- Sends user_id, text, and files to backend

## 2. Backend Layer (Cloud Run – FastAPI)
- FastAPI backend
- Handles REST API routes:
  - /process-text → Generate summary
  - /upload-file → OCR + summary + MCQs + flashcards
  - /generate-mcq-flashcards
- Manages orchestration logic
- Validates input
- Saves/reads from Firestore & Cloud Storage

## 3. Data & Storage Layer
### Firestore
- user notes
- summaries
- MCQs
- flashcards

### Cloud Storage
- uploaded PDFs
- extracted images
- temporary files

### Environment Variables
- GEMINI_API_KEY
- BUCKET_NAME
- GCP_PROJECT

## 4. AI & Context Layer
### Gemini LLM (Gemini 2.5 Flash)
- Summarization
- OCR extraction
- MCQ/flashcard generation
- JSON structuring

### Context Guardrails
- Strict JSON validator
- extract_json()
- Safe fallback logic

## 5. Development & Operations
- Cloud Run deployment pipeline
- Containerized (Dockerfile)
- Local development with uvicorn
