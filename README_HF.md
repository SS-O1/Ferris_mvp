---
title: Ferris AI Travel Booking
emoji: ✈️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Ferris ✈️

> Book your perfect trip in 60 seconds with AI

Ferris eliminates travel booking decision paralysis. Just tell us what you want and get the ONE perfect recommendation.

## 🚀 Quick Start

Visit the Space URL and start chatting!

## ✨ Features

- Natural language search - No filters, just chat
- Single best option - No decision paralysis  
- 60-second booking flow
- Smart AI ranking

## 🛠️ Tech Stack

- Backend: FastAPI, Python 3.11
- Frontend: Vanilla JavaScript
- AI: Google Vertex AI (Gemini)
- TTS: Deepgram API

## 🔑 Required Secrets

Set these in your Space Settings → Repository Secrets:

- `DEEPGRAM_API_KEY` - Your Deepgram API key
- `GCP_PROJECT` - Your Google Cloud project ID
- `GCP_LOCATION` - GCP region (default: us-central1)
- `GEMINI_MODEL_NAME` - Model name (default: gemini-1.5-pro-002)
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Your GCP service account JSON (entire content)

## 👥 Team

Built at UC Berkeley for Calhacks 12.0
