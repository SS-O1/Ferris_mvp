# 🚀 Hugging Face Spaces Deployment Guide

## Step 1: Create a New Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in details:
   - **Space name**: `ferris-ai-travel` (or your choice)
   - **License**: MIT
   - **Select SDK**: Docker
   - **Space hardware**: CPU basic (free) - upgrade if needed
4. Click **"Create Space"**

## Step 2: Configure Secrets (IMPORTANT!)

1. In your new Space, go to **Settings** → **Repository secrets**
2. Add these secrets (click "New secret" for each):

### Required Secrets:

```
Name: DEEPGRAM_API_KEY
Value: [Your Deepgram API key]
```

```
Name: GCP_PROJECT
Value: ferris-476304  (or your GCP project ID)
```

```
Name: GCP_LOCATION
Value: us-central1
```

```
Name: GEMINI_MODEL_NAME
Value: gemini-1.5-pro-002
```

```
Name: GOOGLE_APPLICATION_CREDENTIALS_JSON
Value: [Paste the ENTIRE content of your ferris-476304-0f8e7aba7efc.json file here]
```

**💡 Tip**: For the JSON credential, open `ferris-476304-0f8e7aba7efc.json` and copy ALL of it (from `{` to `}`).

## Step 3: Push Code to HF Spaces

### Option A: Using Git (Recommended)

```bash
# Add HF Spaces as remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ferris-ai-travel

# Push to HF Spaces (this keeps secrets safe!)
git push hf logan2:main
```

### Option B: Upload via Web UI

1. Go to your Space's **Files** tab
2. Click **"Add file"** → **"Upload files"**
3. Drag and drop ALL files EXCEPT:
   - `.env`
   - `ferris-476304-0f8e7aba7efc.json`
   - `node_modules/`
   - `.venv/`

## Step 4: Files to Upload

Make sure these new files are included:
- ✅ `Dockerfile` (created)
- ✅ `app.py` (created)
- ✅ `README_HF.md` → Rename to `README.md` when uploading
- ✅ All your existing app files
- ✅ `requirements.txt`
- ✅ `package.json`
- ✅ `server.js`

## Step 5: Wait for Build

1. HF Spaces will automatically build your Docker container
2. Watch the **Logs** tab for build progress
3. Build time: ~5-10 minutes
4. Once you see "Running on http://0.0.0.0:7860" → You're live! 🎉

## Step 6: Test Your Deployment

1. Visit your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/ferris-ai-travel`
2. The app should load automatically
3. Test the chat interface
4. Verify TTS is working

## 🔧 Troubleshooting

### Build fails?
- Check **Logs** tab for errors
- Verify all secrets are set correctly
- Make sure `Dockerfile` and `app.py` were uploaded

### API errors?
- Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` contains the full JSON
- Check that `GCP_PROJECT` matches your actual project ID
- Confirm `DEEPGRAM_API_KEY` is valid

### Port issues?
- HF Spaces expects port 7860 (already configured in Dockerfile)
- Node server runs on port 3000 internally

## 🎯 Quick Command Reference

```bash
# Clone from HF Spaces
git clone https://huggingface.co/spaces/YOUR_USERNAME/ferris-ai-travel

# Make changes and push
git add .
git commit -m "Update app"
git push hf main

# View logs
# Go to Space UI → Logs tab
```

## 🌟 Next Steps

1. Share your Space URL with users
2. Monitor usage in HF dashboard
3. Upgrade to GPU if needed (for faster inference)
4. Set up custom domain (HF Pro feature)

## ⚠️ Important Notes

- **NEVER** commit `.env` or credential JSON files to ANY git repository
- HF Spaces secrets are encrypted and secure
- Free tier has some rate limits - monitor usage
- Spaces can auto-sleep after inactivity (upgrade to prevent this)

---

Need help? Check [HF Spaces Docs](https://huggingface.co/docs/hub/spaces-overview)
