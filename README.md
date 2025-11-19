# 📘 SmartStudy AI — AI-Powered Learning Assistant

(Google Cloud Run • Gemini AI • Firestore • Cloud Storage)

## 🚀 Overview

SmartStudy AI is an intelligent study assistant that converts text, PDFs, and images into structured learning material using Gemini Flash 2.5.
The backend runs fully on Google Cloud Run, using Firestore and Cloud Storage for persistence.

SmartStudy AI generates:

📝 Summaries

🌟 Key Points

🃏 Flashcards

❓ MCQs

📄 OCR extraction from PDFs & Images

## ✨ Features
📝 Text-to-Summary

Paste any text → Get a clean, AI-generated summary.

📂 File Upload (PDF/Image)

Upload PDFs or images → Gemini extracts text → produces structured notes.

🎯 MCQ & Flashcard Generator

From text or existing saved notes:

5 Flashcards  or  5 MCQs

🎨 Beautiful Frontend

Responsive UI

Sidebar navigation

Dark/Light mode toggle

☁️ Fully Serverless

Runs entirely on:

Cloud Run

Firestore

Cloud Storage

Gemini AI

## 🏗️ Architecture
User → Frontend (HTML + JS)
      → Backend API (FastAPI on Cloud Run)
      → Gemini Flash 2.5 (Summaries, MCQs, Flashcards, OCR)
      → Firestore (notes storage)
      → Cloud Storage (file storage)


![Architecture](smartstudy-architecture.png)

## 🔧 Tech Stack
Frontend

HTML

CSS

JavaScript

Dark & Light Theme

Sidebar Navigation

Backend

Python (FastAPI)

Uvicorn

Google Generative AI SDK

Google Firestore

Google Cloud Storage

Cloud

Cloud Run

Artifact Registry

IAM

Cloud Build

## 🧪 Run Locally

Install dependencies:

pip install -r requirements.txt


Run the backend:

python main.py


Access frontend:

http://localhost:8080

## ☁️ Deploy to Cloud Run

Authenticate:

gcloud auth login
gcloud config set project YOUR_PROJECT_ID


Deploy:

gcloud run deploy smartstudy-ai \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated

## 🔐 Required Environment Variables (Cloud Run)
Variables:

BUCKET_NAME	->             GCS bucket for file storage

GEMINI_API_KEY ->         Gemini Flash API key

GCP_PROJECT	->             Google Cloud project ID
