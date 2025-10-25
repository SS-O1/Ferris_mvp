from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse
from .state import STORE
from .agent_v2 import process_message

app = FastAPI(title="Ferris MVP", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True, "version": "2.0.0"}

@app.get("/", response_class=HTMLResponse)
def landing():
    try:
        with open("static/landing.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Landing page not found</h1>", status_code=404)

@app.get("/demo", response_class=HTMLResponse)
def demo():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Demo not found</h1>", status_code=404)

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    session_id = (req.context.session_id if req.context else None) if req.context else None
    session = STORE.get_session(session_id)
    
    if req.context and req.context.home_airport:
        session.slots.origin = req.context.home_airport.upper()
    
    if message.upper() in ["BOOK", "CONFIRM"]:
        if not session.last_itinerary:
            return ChatResponse(
                text="Nothing to book yet! Tell me where you want to go.",
                itinerary=None,
                state="COLLECTING_SLOTS",
                needed=[]
            )
        
        hold = STORE.place_hold(session.last_itinerary["id"])
        return ChatResponse(
            text=f"🎉 Booked! Confirmation #{hold['hold_id']}\n\n(Demo mode - no real booking)\n\nIn production, this would charge your card and send confirmation email.",
            itinerary=session.last_itinerary,
            state="HOLDING",
            needed=[]
        )
    
    result = process_message(message, session)
    
    return ChatResponse(**result)
