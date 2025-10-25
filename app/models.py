from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field

StateType = Literal[
    "COLLECTING_SLOTS",
    "SEARCHING",
    "PRESENTING_OPTION",
    "AWAITING_REFINEMENT",
    "AWAITING_CONSENT",
    "HOLDING",
    "FAILED"
]

class ChatContext(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    home_airport: Optional[str] = None
    session_id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    context: Optional[ChatContext] = None

class ChatResponse(BaseModel):
    text: str
    itinerary: Optional[Dict[str, Any]] = None
    state: StateType
    needed: List[str] = Field(default_factory=list)

class SessionSlots(BaseModel):
    origin: Optional[str] = None
    party_size: int = 2
    budget_max: Optional[float] = None
    beds_needed: int = 1
    baths_needed: float = 1.0
    transport_pref: Optional[Literal["drive","fly"]] = None
    destination_hint: Optional[str] = None
    cheaper: bool = False
    check_in: Optional[str] = None
    check_out: Optional[str] = None
