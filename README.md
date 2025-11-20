<div align="center">

# 🚀 **SmartStudy AI**
### *AI-Powered Study Material Generator*
Transform notes, PDFs, and documents into **summaries, flashcards, and MCQs** using Google Gemini.

---

### 🔗 **Live Demo (Cloud Run URL)**
👉 _[https://smartstudy-ai.com](https://smartstudy-ai-294186065460.asia-south1.run.app/)_

### 👤 **Author**
**Shyamprasad Puli**

---

### 🌟 Badges

![Static Badge](https://img.shields.io/badge/Made%20with-React-blue?style=for-the-badge&logo=react)
![Static Badge](https://img.shields.io/badge/Backend-FastAPI-green?style=for-the-badge&logo=fastapi)
![Static Badge](https://img.shields.io/badge/Cloud-GoogleCloud-blue?style=for-the-badge&logo=googlecloud)
![Static Badge](https://img.shields.io/badge/AI-Gemini-purple?style=for-the-badge&logo=google)
![Static Badge](https://img.shields.io/badge/Database-Firestore-orange?style=for-the-badge&logo=firebase)

</div>

---

## 📌 **Overview**

**SmartStudy AI** is a cloud-native learning assistant that converts raw study content into structured material.

✔ Summaries  
✔ MCQs  
✔ PDF extraction & OCR  
✔ Stored in Firestore with persistent user notes  


---

## 🧠 **Why SmartStudy AI?**

| Problem | Solution |
|---------|----------|
| Manual note-making is time-consuming | Auto-generate summaries & MCQs |
| Handling multiple file types is complex | Unified upload pipeline handles PDFs, images, raw text |
| Notes not accessible everywhere | Stored securely in Firestore |
| Scaling apps is hard | Cloud Run handles autoscaling |

---

## 🛠 **Tech Stack**

| Layer | Technology |
|-------|------------|
| Frontend | React + Tailwind |
| Backend | FastAPI |
| AI Engine | Gemini API |
| Storage | Cloud Storage |
| Database | Firestore |
| Hosting | Cloud Run |

---

## 🧩 **Features**

- ✨ Upload PDFs/images → extract content
- 🔍 Summarization using Gemini
- 📝 MCQs for revision
- ☁ Cloud Run serverless backend
- 🔐 Stored securely in Firestore

---

## 🏗 **Setup & Installation**

### **1️⃣ Clone Repo**

```bash
git clone https://github.com/yourusername/smartstudy-ai.git
cd smartstudy-ai
```
---

### **2️⃣ Backend Setup**
```bash
Copy code
pip install -r requirements.txt
uvicorn main:app --reload
```
### **3️⃣ Frontend Setup**
```bash
Copy code
npm install
npm run dev
```

### **🔐 Environment Variables**

Create a .env file locally:
```bash
GEMINI_API_KEY=YOUR_KEY
BUCKET_NAME=your-bucket
GCP_PROJECT=your-project-id
PORT=8080
```

### **☁ Deploy to Cloud Run**
```bash
Copy code
gcloud builds submit --tag gcr.io/$PROJECT_ID/smartstudy
gcloud run deploy smartstudy-ai \
--image gcr.io/$PROJECT_ID/smartstudy \
--allow-unauthenticated
```
6️⃣ Create Storage Bucket
```bash
export PROJECT_ID=<your-id>
export REGION=us-central1
export BUCKET_NAME=<your-bucket>
```
Create a bucket in console or:

```bash
Copy code
gsutil mb -l $REGION gs://$BUCKET_NAME
```

7️⃣ Build Docker Image
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/smartstudy
```
8️⃣ Deploy to Cloud Run
```bash
gcloud run deploy smartstudy \
--image gcr.io/$PROJECT_ID/smartstudy \
--allow-unauthenticated \
--region=$REGION
```
<div align="center"> Made by <b>Shyamprasad Puli</b> </div> ```





