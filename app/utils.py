from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Tuple, Optional
import math
import re
from dateutil import tz

PACIFIC = tz.gettz("America/Los_Angeles")

def resolve_weekend(today: Optional[date] = None) -> Tuple[date, date]:
    """Return next Fri–Sun for America/Los_Angeles."""
    if today is None:
        today = datetime.now(PACIFIC).date()
    days_until_fri = (4 - today.weekday()) % 7
    if days_until_fri == 0 and datetime.now(PACIFIC).hour >= 18:
        pass
    check_in = today + timedelta(days=days_until_fri)
    check_out = check_in + timedelta(days=2)
    return check_in, check_out

def iso_today_pacific() -> str:
    return datetime.now(PACIFIC).isoformat()

def parse_money(text: str) -> Optional[float]:
    m = re.search(r'under\s*\$?\s*(\d{2,5})', text, re.I)
    if m: return float(m.group(1))
    m = re.search(r'budget\s*\$?\s*(\d{2,5})', text, re.I)
    if m: return float(m.group(1))
    m = re.search(r'\$\s*(\d{2,5})', text)
    if m: return float(m.group(1))
    return None

def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c
