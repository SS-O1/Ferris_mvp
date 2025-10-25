from __future__ import annotations
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from .models import SessionSlots

@dataclass
class Session:
    session_id: str
    slots: SessionSlots = field(default_factory=SessionSlots)
    state: str = "COLLECTING_SLOTS"
    last_itinerary: Optional[dict] = None

class MemoryStore:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.holds: Dict[str, dict] = {}

    def get_session(self, session_id: Optional[str]) -> Session:
        sid = session_id or "default"
        if sid not in self.sessions:
            self.sessions[sid] = Session(session_id=sid)
        return self.sessions[sid]

    def place_hold(self, itinerary_id: str) -> dict:
        hold_id = f"HOLD_{itinerary_id}"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        hold = {"hold_id": hold_id, "expires_at": expires_at, "itinerary_id": itinerary_id}
        self.holds[hold_id] = hold
        return hold

STORE = MemoryStore()
