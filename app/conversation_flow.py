from __future__ import annotations
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dateutil import tz

PACIFIC = tz.gettz("America/Los_Angeles")

class ConversationState(Enum):
    INITIAL = "initial"
    NEED_LOCATION = "need_location"
    NEED_DATES = "need_dates"
    NEED_CUSTOM_DATES = "need_custom_dates"
    NEED_GUESTS = "need_guests"
    READY_TO_SEARCH = "ready_to_search"
    SHOWING_RESULT = "showing_result"
    REFINING = "refining"

class ConversationContext:
    def __init__(self):
        self.state = ConversationState.INITIAL
        self.slots = {
            "destination": None,
            "activity": None,
            "check_in": None,
            "check_out": None,
            "guests": None,
            "budget_max": None,
            "vibe": None,
        }
        self.refinement_preferences = []
        self.shown_properties = []
        self.waiting_for_custom_dates = False
        
    def extract_activity(self, message: str) -> Optional[str]:
        """Extract activity type from message"""
        msg = message.lower()
        activities = {
            "beach": ["beach", "ocean", "surf", "coastal", "sand", "seaside"],
            "ski": ["ski", "skiing", "snowboard", "snow", "winter sports"],
            "wine": ["wine", "vineyard", "winery", "tasting", "wine country"],
            "hiking": ["hike", "hiking", "trail", "nature", "outdoors", "mountains"],
            "city": ["city", "urban", "downtown", "nightlife", "restaurants"],
            "relaxing": ["relax", "peaceful", "quiet", "spa", "retreat"],
        }
        for activity, keywords in activities.items():
            if any(kw in msg for kw in keywords):
                return activity
        return None
    
    def missing_critical_slots(self) -> List[str]:
        """Return required slots that are missing"""
        missing = []
        if not self.slots["destination"]:
            missing.append("destination")
        if not self.slots["check_in"]:
            missing.append("dates")
        if not self.slots["guests"]:
            missing.append("guests")
        return missing
    
    def is_ready_to_search(self) -> bool:
        """Can we search with current data?"""
        return bool(
            self.slots["destination"] and 
            self.slots["check_in"] and 
            self.slots["guests"]
        )

def get_destinations_for_activity(activity: str) -> List[str]:
    """Return relevant destinations based on activity"""
    mapping = {
        "beach": ["San Diego", "Santa Cruz", "Malibu", "Monterey", "Santa Barbara"],
        "ski": ["Lake Tahoe", "Mammoth Lakes", "Big Bear", "Tahoe City"],
        "wine": ["Napa", "Sonoma", "Paso Robles", "Healdsburg"],
        "hiking": ["Yosemite", "Big Sur", "Joshua Tree", "Sequoia"],
        "city": ["San Francisco", "Los Angeles", "San Diego", "Oakland"],
        "relaxing": ["Big Sur", "Carmel", "Mendocino", "Ojai"],
    }
    return mapping.get(activity, ["San Diego", "Lake Tahoe", "Napa", "Big Sur", "San Francisco"])

def generate_clarification(context: ConversationContext, message: str) -> Dict[str, Any]:
    """Generate next clarification question based on context"""
    
    msg_lower = message.lower()
    
    # Check if user wants to type custom dates
    if context.waiting_for_custom_dates or "i have specific" in msg_lower or "specific dates" in msg_lower or "custom dates" in msg_lower:
        context.waiting_for_custom_dates = False
        return {
            "action": "clarify",
            "question": "Great! Please type your dates (e.g., 'Nov 15-17' or 'December 1-3'):",
            "quick_replies": [],
            "collecting": "custom_dates",
            "context": context
        }
    
    # Extract activity if not set
    if not context.slots["activity"]:
        context.slots["activity"] = context.extract_activity(message)
    
    # Check what we still need
    missing = context.missing_critical_slots()
    
    if not missing:
        return {"action": "search", "context": context}
    
    # Ask for destination
    if "destination" in missing:
        if "somewhere else" in msg_lower or "different" in msg_lower:
            all_destinations = [
                "San Diego", "Lake Tahoe", "Napa", "Big Sur", "San Francisco",
                "Santa Barbara", "Monterey", "Joshua Tree", "Carmel", "Sonoma"
            ]
            return {
                "action": "clarify",
                "question": "Great! Here are some wonderful destinations:",
                "quick_replies": all_destinations[:8],
                "collecting": "destination",
                "context": context
            }
        
        if context.slots["activity"]:
            suggestions = get_destinations_for_activity(context.slots["activity"])
            suggestions.append("Somewhere else")
            return {
                "action": "clarify",
                "question": "Perfect! Where would you like to go?",
                "quick_replies": suggestions[:6],
                "collecting": "destination",
                "context": context
            }
        else:
            return {
                "action": "clarify",
                "question": "Where would you like to go?",
                "quick_replies": ["San Diego", "Lake Tahoe", "Napa", "Big Sur", "Somewhere else"],
                "collecting": "destination",
                "context": context
            }
    
    # Ask for dates
    if "dates" in missing:
        dest = context.slots["destination"]
        return {
            "action": "clarify",
            "question": f"When are you thinking for {dest}?",
            "quick_replies": ["This weekend", "Next weekend", "I have specific dates"],
            "collecting": "dates",
            "context": context
        }
    
    # Ask for party size
    if "guests" in missing:
        return {
            "action": "clarify",
            "question": "How many people will be joining?",
            "quick_replies": ["Just me", "2 people", "3-4 people", "5-6 people", "Large group (7+)"],
            "collecting": "guests",
            "context": context
        }
    
    return {"action": "search", "context": context}

def resolve_date_input(date_str: str) -> tuple:
    """Convert user input to check_in, check_out dates with fuzzy matching"""
    today = datetime.now(PACIFIC).date()
    msg = date_str.lower().strip()
    
    # Handle simple presets
    if "this weekend" in msg:
        days_until_fri = (4 - today.weekday()) % 7
        if days_until_fri == 0 and datetime.now(PACIFIC).hour >= 12:
            days_until_fri = 7
        check_in = today + timedelta(days=days_until_fri if days_until_fri > 0 else 7)
        check_out = check_in + timedelta(days=2)
        return check_in.isoformat(), check_out.isoformat()
    
    elif "next weekend" in msg:
        days_until_fri = (4 - today.weekday()) % 7
        check_in = today + timedelta(days=days_until_fri + 7)
        check_out = check_in + timedelta(days=2)
        return check_in.isoformat(), check_out.isoformat()
    
    # Parse custom dates with fuzzy month matching
    import re
    from dateutil.parser import parse as parse_date
    
    # Fuzzy month matching (handles typos)
    month_map = {
        "jan": "January", "januar": "January", "january": "January",
        "feb": "February", "februar": "February", "february": "February",
        "mar": "March", "march": "March",
        "apr": "April", "april": "April",
        "may": "May",
        "jun": "June", "june": "June",
        "jul": "July", "july": "July",
        "aug": "August", "august": "August",
        "sep": "September", "sept": "September", "september": "September",
        "oct": "October", "october": "October",
        "nov": "November", "novem": "November", "november": "November",
        "dec": "December", "decem": "December", "december": "December"
    }
    
    # Try pattern: "Month Day-Day" (e.g., "Januar 1-15", "Nov 15-17")
    range_pattern = r'([a-z]+)\s+(\d+)\s*[-–]\s*(\d+)'
    match = re.search(range_pattern, msg)
    
    if match:
        try:
            month_input = match.group(1).lower()
            start_day = int(match.group(2))
            end_day = int(match.group(3))
            
            # Fuzzy match the month
            month_name = None
            for key, value in month_map.items():
                if month_input.startswith(key[:3]):  # Match first 3 letters
                    month_name = value
                    break
            
            if not month_name:
                # Try exact match
                for key, value in month_map.items():
                    if key in month_input:
                        month_name = value
                        break
            
            if month_name:
                # Parse dates
                check_in = parse_date(f"{month_name} {start_day} {today.year}")
                check_out = parse_date(f"{month_name} {end_day} {today.year}")
                
                # If dates are in the past, assume next year
                if check_in.date() < today:
                    check_in = check_in.replace(year=today.year + 1)
                    check_out = check_out.replace(year=today.year + 1)
                
                return check_in.date().isoformat(), check_out.date().isoformat()
        except Exception as e:
            print(f"Date parsing error: {e}")
    
    # Try numerical format: "1/15-1/17", "01/15-01/17"
    numeric_pattern = r'(\d{1,2})/(\d{1,2})\s*[-–]\s*(\d{1,2})/(\d{1,2})'
    match = re.search(numeric_pattern, msg)
    
    if match:
        try:
            start_month = int(match.group(1))
            start_day = int(match.group(2))
            end_month = int(match.group(3))
            end_day = int(match.group(4))
            
            check_in_date = datetime(today.year, start_month, start_day).date()
            check_out_date = datetime(today.year, end_month, end_day).date()
            
            if check_in_date < today:
                check_in_date = datetime(today.year + 1, start_month, start_day).date()
                check_out_date = datetime(today.year + 1, end_month, end_day).date()
            
            return check_in_date.isoformat(), check_out_date.isoformat()
        except Exception as e:
            print(f"Numeric date parsing error: {e}")
    
    # Default to next weekend if all parsing fails
    print(f"Could not parse date: {date_str}, defaulting to next weekend")
    days_until_fri = (4 - today.weekday()) % 7
    check_in = today + timedelta(days=days_until_fri if days_until_fri > 0 else 7)
    check_out = check_in + timedelta(days=2)
    return check_in.isoformat(), check_out.isoformat()


def parse_guest_count(guest_str: str) -> int:
    """Extract guest count from user input"""
    msg = guest_str.lower()
    if "just me" in msg or "solo" in msg or "1" in msg:
        return 1
    elif "2" in msg or "two" in msg or "couple" in msg:
        return 2
    elif "3" in msg or "three" in msg or "3-4" in msg:
        return 3
    elif "4" in msg or "four" in msg:
        return 4
    elif "5" in msg or "five" in msg or "5-6" in msg:
        return 5
    elif "6" in msg or "six" in msg:
        return 6
    elif "large" in msg or "7+" in msg or "7" in msg:
        return 8
    
    import re
    numbers = re.findall(r'\d+', msg)
    if numbers:
        return int(numbers[0])
    
    return 2
