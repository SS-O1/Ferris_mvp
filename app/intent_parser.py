from __future__ import annotations
import re
from typing import Dict, Any
from datetime import datetime, timedelta
from dateutil import tz

PACIFIC = tz.gettz("America/Los_Angeles")

def parse_intent(message: str) -> Dict[str, Any]:
    """Extract destination, activity, dates, guests, budget from message"""
    msg = message.lower().strip()
    intent = {
        "destination": None,
        "activity": None,
        "check_in": None,
        "check_out": None,
        "guests": 2,
        "budget_max": None
    }
    
    # Destinations
    destinations = [
        "tahoe", "lake tahoe", "south lake tahoe", "north lake tahoe",
        "san diego", "la jolla", "coronado",
        "napa", "napa valley", "sonoma",
        "big sur", "carmel", "monterey",
        "santa barbara", "santa cruz",
        "joshua tree", "palm springs",
        "yosemite", "mammoth", "mammoth lakes",
        "san francisco", "oakland", "berkeley",
        "los angeles", "malibu", "venice",
    ]
    
    for dest in destinations:
        if dest in msg:
            intent["destination"] = dest.title()
            break
    
    # Activities
    activities = {
        "ski": ["ski", "skiing", "snowboard"],
        "beach": ["beach", "ocean", "surf", "coastal"],
        "wine": ["wine", "vineyard", "winery", "tasting"],
        "hiking": ["hike", "hiking", "trail", "outdoor"],
        "city": ["city", "urban", "downtown", "nightlife"],
    }
    
    for activity, keywords in activities.items():
        if any(kw in msg for kw in keywords):
            intent["activity"] = activity
            break
    
    # Dates
    if "this weekend" in msg:
        ci, co = _resolve_next_weekend()
        intent["check_in"] = ci.isoformat()
        intent["check_out"] = co.isoformat()
    elif "next weekend" in msg:
        ci, co = _resolve_next_weekend()
        ci += timedelta(days=7)
        co += timedelta(days=7)
        intent["check_in"] = ci.isoformat()
        intent["check_out"] = co.isoformat()
    else:
        ci, co = _resolve_next_weekend()
        intent["check_in"] = ci.isoformat()
        intent["check_out"] = co.isoformat()
    
    # Party size
    match = re.search(r'(\d+)\s*(people|guests|adults|person)', msg)
    if match:
        intent["guests"] = int(match.group(1))
    
    # Budget
    match = re.search(r'under\s*\$?(\d+)', msg)
    if match:
        intent["budget_max"] = float(match.group(1))
    match = re.search(r'budget\s*\$?(\d+)', msg)
    if match:
        intent["budget_max"] = float(match.group(1))
    
    return intent

def _resolve_next_weekend():
    """Return next Friday-Sunday"""
    today = datetime.now(PACIFIC).date()
    days_until_fri = (4 - today.weekday()) % 7
    
    if days_until_fri == 0 and datetime.now(PACIFIC).hour >= 18:
        days_until_fri = 7
    
    check_in = today + timedelta(days=days_until_fri if days_until_fri > 0 else 7)
    check_out = check_in + timedelta(days=2)
    return check_in, check_out
