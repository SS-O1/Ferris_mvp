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
```

**Save:** Cmd + S

***

## ⏰ PHASE 5: GIT & GITHUB (6:00 AM - 6:30 AM)

### Step 19: Initialize Git

**In VS Code terminal:**

```bash
# Initialize Git
git init

# Check what will be committed
git status
# Should show all files EXCEPT .venv/ and .env (those are in .gitignore)

# Add all files
git add .

# First commit
git commit -m "Initial commit: Ferris MVP - AI travel booking"
```

### Step 20: Create GitHub Repo

**Option A: Using GitHub CLI (Fastest)**

```bash
# Install if needed
brew install gh

# Login (will open browser)
gh auth login
# Choose: GitHub.com → HTTPS → Yes → Login with browser

# Create repo and push
gh repo create Ferris-mvp --public --source=. --remote=origin --push

# Done! Your code is now at github.com/YOUR_USERNAME/Ferris-mvp
```

**Option B: Manual**

1. Go to [**https://github.com/new**](https://github.com/new) in browser
2. Repository name: `Ferris-mvp`
3. Description: `AI-powered travel booking in 60 seconds`
4. Public
5. Do NOT check "Initialize with README"
6. Click "Create repository"

Then in terminal:

```bash
git remote add origin https://github.com/YOUR_USERNAME/Ferris-mvp.git
git branch -M main
git push -u origin main
```

### Step 21: Add Repo Details

On GitHub repo page:
1. Click ⚙️ next to "About"
2. Description: `AI-powered travel booking in 60 seconds - YC W25`
3. Topics: `ai`, `travel`, `fastapi`, `python`, `hackathon`
4. Save

***

## ⏰ PHASE 6: DEPLOY (6:30 AM - 7:00 AM)

### Step 22: Deploy to Railway

**In VS Code terminal:**

```bash
# Install Railway CLI
brew install railway

# Login
railway login
# Opens browser, login with GitHub

# Initialize project
railway init
# Project name: Ferris-mvp
# Choose: Empty project

# Deploy
railway up

# Get your URL
railway domain
# Generates URL like: Ferris-mvp-production.up.railway.app
```

**Copy that URL!** You'll need it for YC application.

### Step 23: Test Deployment

Open your Railway URL in browser (something like `https://Ferris-mvp-production.up.railway.app`)

Should see your landing page live!

***

## ⏰ PHASE 7: DEMO VIDEO (7:00 AM - 7:30 AM)

### Step 24: Record Demo

1. **Open QuickTime** (Cmd + Space, type "QuickTime")
2. **File** → **New Screen Recording**
3. Click red record button
4. **Record this flow** (60 seconds):
   - Open your Railway URL
   - Show landing page (5 sec)
   - Click "Try it now"
   - Type "beach weekend in San Diego under $400"
   - Show result (10 sec)
   - Type "BOOK"
   - Show confirmation (5 sec)
5. **Stop** recording (click stop in menu bar)
6. **File** → **Export As** → Save to Desktop as `Ferris-demo.mov`

### Step 25: Upload Video

**Option A: Loom (Easiest)**
1. Go to [**https://www.loom.com/**](https://www.loom.com/)
2. Sign up free
3. Click "Upload"
4. Upload `Ferris-demo.mov`
5. Copy the link

**Option B: YouTube**
1. Go to [**https://studio.youtube.com/**](https://studio.youtube.com/)
2. Create → Upload video
3. Upload `Ferris-demo.mov`
4. Visibility: **Unlisted**
5. Copy the link

***

## ⏰ PHASE 8: YC APPLICATION (7:30 AM - 9:00 AM)

### Step 26: Fill Out YC Application

Go to: [**https://www.ycombinator.com/apply**](https://www.ycombinator.com/apply)

**Key Fields:**

**Company name:** Ferris

**Company URL:** [Your Railway URL]

**Demo video:** [Your Loom/YouTube URL]

**What is your company going to make?**
```
Ferris uses AI to book travel in 60 seconds. Type "beach weekend under $500", get the perfect Airbnb, book. No scrolling through 500 options, no decision paralysis. This is Uber for travel booking—press button, get trip.
```

**Why did you pick this idea?**
```
I spent 45 minutes last weekend comparing 200+ Airbnbs in Tahoe. Ended up booking the first one I looked at. This is broken. Airbnb's 7M listings create decision paralysis. AI can eliminate choice overload and give you THE right answer instantly.
```

**What's new about what you're making?**
```
We're the first to use AI for single-option travel recommendations (not just smarter search). Decision paralysis is the actual problem—Airbnb's 7M listings are a bug, not a feature. We show 1 perfect option vs 500 mediocre ones.
```

**How far along are you?**
```
Working MVP deployed at [Railway URL]. Code open-sourced at [GitHub URL]. Users can search, get AI recommendations, and book (demo mode) in under 60 seconds. Built in 36 hours.
```

**How long have each of you been working on this?**
```
36 hours as of submission. Started Friday 10 PM, deployed Sunday morning.
```

**Link to GitHub:** https://github.com/YOUR_USERNAME/Ferris-mvp

### Step 27: Submit!

Click **Submit Application**

***

## ⏰ PHASE 9: FINAL POLISH (9:00 AM - 10:00 AM)

### Step 28: Update README with Live URL

**In VS Code, edit `README.md`:**

Add at top:
```markdown
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://your-actual-railway-url.up.railway.app)

**🚀 Live Demo:** https://your-actual-railway-url.up.railway.app
```

**Save and push:**

```bash
git add README.md
git commit -m "Add live demo URL"
git push
```

### Step 29: Share on Social

**Twitter/X post:**
```
Just built Ferris in 36 hours 🚀

Book travel in 60 seconds with AI. No more scrolling through 500 Airbnbs.

Try it: [your Railway URL]
Demo: [your video URL]

Built for @ycombinator W25. Feedback welcome! 🙏
```

### Step 30: Test on Phone

Open your Railway URL on your phone → should work responsively!

***

## ✅ FINAL CHECKLIST

Before 10 AM Sunday:

- [ ] ✅ App works locally (tested at http://127.0.0.1:8000)
- [ ] ✅ Code pushed to GitHub (public repo)
- [ ] ✅ App deployed to Railway (live URL)
- [ ] ✅ README has live demo link
- [ ] ✅ Demo video recorded and uploaded
- [ ] ✅ YC application submitted
- [ ] ✅ Tested on phone (mobile works)
- [ ] ✅ Shared on Twitter/social

***

## 🚨 TROUBLESHOOTING

**"ModuleNotFoundError"**
```bash
# Make sure venv is activated
source .venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

**"Port 8000 already in use"**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**"Application startup failed"**
```bash
# Check for syntax errors
python3 -m py_compile app/main.py

# Check logs in terminal for specific error
```

**Frontend not loading**
```bash
# Check files exist
ls static/

# Make sure server is running
# Check terminal for errors
```

**Railway deployment fails**
```bash
# Check you have all files committed
git status

# Make sure requirements.txt is correct
cat requirements.txt
```

***

## 🎯 YOU NOW HAVE THE COMPLETE PATH

**Start NOW at Step 1.** Work through sequentially.

**Timeline:**
- 2:07 AM - Start
- 4:30 AM - Backend working
- 5:30 AM - Frontend working
- 6:30 AM - GitHub done
- 7:00 AM - Deployed
- 7:30 AM - Demo recorded
- 9:00 AM - YC submitted
- 10:00 AM - DONE! ✅

**You have everything you need. GO BUILD! 🚀**

Questions? Share your error messages and current step number.
