"""
Startup script for Hugging Face Spaces deployment.
This ensures Google Cloud credentials are properly configured from secrets.
"""
import os
import json
import subprocess
import sys
from pathlib import Path

def setup_gcp_credentials():
    """Setup Google Cloud credentials from HF Spaces secrets."""
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    if creds_json:
        # Write credentials to a file
        creds_path = Path("/tmp/gcp-credentials.json")
        try:
            # Parse to validate JSON
            creds_data = json.loads(creds_json)
            creds_path.write_text(json.dumps(creds_data, indent=2))
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
            print("✅ Google Cloud credentials configured successfully")
        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            print("Vertex AI features may not work properly")
    else:
        print("⚠️ Warning: GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
        print("Vertex AI features will not work")
    
    # Verify other required environment variables
    required_vars = ["GCP_PROJECT", "DEEPGRAM_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing)}")
    else:
        print("✅ All required environment variables are set")

def start_node_server():
    """Start Node.js server in background."""
    print("🚀 Starting Node.js TTS server on port 3000...")
    node_process = subprocess.Popen(
        ["node", "server.js"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return node_process

def start_fastapi():
    """Start FastAPI server."""
    print("🚀 Starting FastAPI server on port 7860...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"])

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 Ferris AI Travel Booking - Starting up...")
    print("=" * 60)
    
    # Setup credentials
    setup_gcp_credentials()
    
    # Start Node.js server
    node_proc = start_node_server()
    
    # Start FastAPI (this will replace current process)
    start_fastapi()
