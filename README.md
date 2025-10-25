# Ferris ✈️

> Book your perfect trip in 60 seconds with AI

## 🎯 What is Ferris?

Ferris eliminates travel booking decision paralysis. Instead of scrolling through 500+ Airbnb listings, just tell us what you want:

- "Beach weekend in San Diego under $500"
- "Skiing in Tahoe this weekend"  

Our AI finds **the ONE perfect place** and you book in 60 seconds.

## 🚀 Quick Start

```
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload

# Visit
open http://127.0.0.1:8000
```

## ✨ Features

- Natural language search - No filters, just chat
- Single best option - No decision paralysis
- 60-second booking flow
- Smart AI ranking

## 🛠️ Tech Stack

- Backend: FastAPI, Python 3.11
- Frontend: Vanilla JavaScript
- Data: Mock Airbnb listings (demo)
- Deployment: Railway

## 📦 Project Structure

```
Ferris_mvp/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── agent_v2.py          # AI agent logic
│   ├── intent_parser.py     # NLP intent extraction
│   ├── ranker.py            # Listing scoring
│   └── airbnb_scraper.py    # Data source
├── static/
│   ├── landing.html         # Homepage
│   └── index.html           # Chat interface
└── requirements.txt
```

## 🎮 Usage

1. Visit homepage
2. Click "Try it now"
3. Type: "beach weekend in San Diego under $500"
4. Get instant recommendation
5. Type "BOOK" to confirm

## 👥 Team

Built at UC Berkeley for Calhacks 12.0

