from __future__ import annotations
from typing import Dict, Any
from .conversation_flow import (
    ConversationContext, 
    generate_clarification,
    resolve_date_input,
    parse_guest_count
)
from .intent_parser import parse_intent
from .airbnb_scraper import search_airbnb
from .ranker import rank_listings

def process_message(message: str, session: Any) -> Dict[str, Any]:
    """
    Enhanced agent with conversation flow
    """
    
    # Initialize conversation context if not exists
    if not hasattr(session, 'conversation_context'):
        session.conversation_context = ConversationContext()
    
    context = session.conversation_context
    msg_lower = message.lower().strip()
    
    # Handle refinement requests
    if context.state.value == "showing_result" and hasattr(session, 'last_itinerary'):
        if any(word in msg_lower for word in ["cheaper", "budget", "less expensive", "too expensive"]):
            return handle_refinement(session, "cheaper")
        elif any(word in msg_lower for word in ["bigger", "more beds", "more space"]):
            return handle_refinement(session, "bigger")
        elif any(word in msg_lower for word in ["different", "something else", "another", "other option"]):
            return handle_refinement(session, "different")
    
    # Update context with new message
    update_context_from_message(context, message)
    
    # Check if we need to clarify
    if not context.is_ready_to_search():
        clarification = generate_clarification(context, message)
        
        if clarification["action"] == "clarify":
            return {
                "text": clarification["question"],
                "itinerary": None,
                "state": "COLLECTING_SLOTS",
                "needed": [clarification["collecting"]],
                "quick_replies": clarification.get("quick_replies", [])
            }
    
    # Ready to search!
    return execute_search(context, session)

def update_context_from_message(context: ConversationContext, message: str):
    """Extract and update slots from user message"""
    msg = message.lower()
    
    # If we're waiting for custom dates or user entered something with numbers, try to parse as date
    if context.waiting_for_custom_dates or (not context.slots["check_in"] and any(char.isdigit() for char in msg)):
        # Check if it looks like a date input (has month name or numbers)
        looks_like_date = any(month in msg for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]) or "/" in msg or "-" in msg
        
        if looks_like_date:
            context.waiting_for_custom_dates = False
            try:
                check_in, check_out = resolve_date_input(message)
                context.slots["check_in"] = check_in
                context.slots["check_out"] = check_out
                return  # Exit early after parsing dates
            except Exception as e:
                print(f"Date parsing failed: {e}")
                # Continue to other parsing if date parsing fails
    
    # Update destination - more comprehensive
    destinations = [
        "san diego", "lake tahoe", "tahoe", "napa", "big sur", "santa cruz",
        "malibu", "monterey", "yosemite", "mammoth", "joshua tree", "sonoma",
        "san francisco", "los angeles", "santa barbara", "carmel", "mendocino",
        "ojai", "healdsburg", "paso robles", "sequoia", "oakland", "tahoe city", "big bear"
    ]
    for dest in destinations:
        if dest in msg:
            if dest == "tahoe":
                context.slots["destination"] = "Lake Tahoe"
            elif dest == "sf" or dest == "san francisco":
                context.slots["destination"] = "San Francisco"
            elif dest == "la" or dest == "los angeles":
                context.slots["destination"] = "Los Angeles"
            else:
                context.slots["destination"] = dest.title()
            break
    
    # Update dates with simple keywords
    if any(word in msg for word in ["this weekend", "next weekend", "weekend", "flexible"]):
        check_in, check_out = resolve_date_input(message)
        context.slots["check_in"] = check_in
        context.slots["check_out"] = check_out
    
    # Update guests - comprehensive extraction
    if any(word in msg for word in ["people", "guests", "person", "just me", "solo", "couple", "group", "family"]):
        context.slots["guests"] = parse_guest_count(message)
    
    # Also check for standalone numbers that might be guest count
    import re
    if context.slots["guests"] is None:
        numbers = re.findall(r'\b(\d+)\s*(?:people|guests|adults|persons?)\b', msg)
        if numbers:
            context.slots["guests"] = int(numbers[0])
    
    # Update budget
    budget_match = re.search(r'under\s*\$?(\d+)', msg)
    if budget_match:
        context.slots["budget_max"] = float(budget_match.group(1))
    budget_match2 = re.search(r'budget\s*\$?(\d+)', msg)
    if budget_match2:
        context.slots["budget_max"] = float(budget_match2.group(1))


def execute_search(context: ConversationContext, session: Any) -> Dict[str, Any]:
    """Execute search and return THE recommendation"""
    
    listings = search_airbnb(
        destination=context.slots["destination"],
        check_in=context.slots["check_in"],
        check_out=context.slots["check_out"],
        guests=context.slots["guests"]
    )
    
    if not listings:
        return {
            "text": f"Hmm, I couldn't find available places in {context.slots['destination']} for those dates. Try different dates?",
            "itinerary": None,
            "state": "FAILED",
            "needed": [],
            "quick_replies": ["This weekend", "Next weekend", "Different location"]
        }
    
    # Rank and get THE best one
    origin = getattr(session.slots, 'origin', 'SFO') if hasattr(session, 'slots') else "SFO"
    
    # Build intent for ranker
    intent = {
        "destination": context.slots["destination"],
        "check_in": context.slots["check_in"],
        "check_out": context.slots["check_out"],
        "guests": context.slots["guests"],
        "budget_max": context.slots.get("budget_max")
    }
    
    ranked = rank_listings(listings, intent, origin)
    best = ranked[0]
    
    # Store for refinement
    context.shown_properties.append(best["id"])
    context.state = ConversationState.SHOWING_RESULT
    
    # Calculate pricing
    from datetime import datetime
    check_in_date = datetime.fromisoformat(context.slots["check_in"])
    check_out_date = datetime.fromisoformat(context.slots["check_out"])
    nights = (check_out_date - check_in_date).days
    total_price = best["price_per_night"] * nights
    
    # Build itinerary
    itinerary = {
        "id": best["id"],
        "destination": context.slots["destination"],
        "name": best["name"],
        "dates": {
            "check_in": context.slots["check_in"],
            "check_out": context.slots["check_out"]
        },
        "stay": {
            "name": best["name"],
            "beds": best["beds"],
            "baths": best["baths"],
            "price_per_night": best["price_per_night"],
            "price_total": total_price,
            "rating": best["rating"],
            "review_count": best["review_count"],
            "image_url": best["image_url"],
            "url": best["url"],
            "amenities": best["amenities"],
            "cancellation_policy": best["cancellation_policy"],
            "guests_max": best["guests_max"]
        },
        "total_price": total_price,
        "currency": "USD",
        "nights": nights,
        "why_this_property": generate_recommendation_reason(best, context)
    }
    
    session.last_itinerary = itinerary
    
    # Build response
    why_text = itinerary["why_this_property"]
    text = f"Found THE perfect spot for you! 🎯\n\n**{best['name']}**\n\n{why_text}\n\n"
    text += f"💰 ${total_price:.0f} total ({nights} nights × ${best['price_per_night']:.0f})\n"
    text += f"🛏️ {best['beds']} beds, {best['baths']} baths\n"
    text += f"⭐ {best['rating']}/5 ({best['review_count']} reviews)\n\n"
    text += f"Type **BOOK** to reserve, or ask for something different!"
    
    return {
        "text": text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": [],
        "quick_replies": ["BOOK", "Too expensive", "Want more space", "Different area"]
    }

def generate_recommendation_reason(property_data: Dict, context: ConversationContext) -> str:
    """Generate personalized 'why this property' explanation"""
    reasons = []
    
    # Location-based
    if property_data.get("coords"):
        reasons.append(f"Prime location in {context.slots['destination']}")
    
    # Capacity
    if property_data["guests_max"] >= context.slots["guests"]:
        if context.slots["guests"] > 2:
            reasons.append(f"Comfortably fits your group of {context.slots['guests']}")
        else:
            reasons.append("Perfect for couples")
    
    # Rating
    if property_data["rating"] >= 4.7:
        reasons.append(f"Highly rated ({property_data['rating']}/5)")
    
    # Budget
    if context.slots.get("budget_max"):
        nights = 2  # Default weekend
        total = property_data["price_per_night"] * nights
        if total <= context.slots["budget_max"]:
            under = context.slots["budget_max"] - total
            reasons.append(f"Under budget (saves you ${under:.0f})")
    
    return " • ".join(reasons[:3])  # Top 3 reasons

def handle_refinement(session: Any, refinement_type: str) -> Dict[str, Any]:
    """Handle user refinement requests"""
    
    context = session.conversation_context
    previous = session.last_itinerary
    
    # Get all listings again
    listings = search_airbnb(
        destination=context.slots["destination"],
        check_in=context.slots["check_in"],
        check_out=context.slots["check_out"],
        guests=context.slots["guests"]
    )
    
    # Filter out shown properties
    available = [l for l in listings if l["id"] not in context.shown_properties]
    
    if not available:
        return {
            "text": "That's all I have for those criteria. Want to try different dates or location?",
            "itinerary": previous,
            "state": "AWAITING_CONSENT",
            "needed": [],
            "quick_replies": ["Different dates", "Different location", "Book current"]
        }
    
    # Apply refinement
    if refinement_type == "cheaper":
        available.sort(key=lambda x: x["price_per_night"])
        best = available[0]
        tradeoff = f"${previous['total_price'] - (best['price_per_night'] * previous['nights']):.0f} cheaper"
    
    elif refinement_type == "bigger":
        available.sort(key=lambda x: x["beds"], reverse=True)
        best = available[0]
        tradeoff = f"{best['beds']} beds (vs {previous['stay']['beds']})"
    
    else:  # different
        best = available[0]
        tradeoff = "Different area"
    
    # Mark as shown
    context.shown_properties.append(best["id"])
    
    # Build new itinerary
    nights = previous["nights"]
    total_price = best["price_per_night"] * nights
    
    itinerary = {
        "id": best["id"],
        "destination": context.slots["destination"],
        "name": best["name"],
        "dates": previous["dates"],
        "stay": {
            "name": best["name"],
            "beds": best["beds"],
            "baths": best["baths"],
            "price_per_night": best["price_per_night"],
            "price_total": total_price,
            "rating": best["rating"],
            "review_count": best["review_count"],
            "image_url": best["image_url"],
            "url": best["url"],
            "amenities": best["amenities"],
            "cancellation_policy": best["cancellation_policy"],
            "guests_max": best["guests_max"]
        },
        "total_price": total_price,
        "currency": "USD",
        "nights": nights,
        "why_this_property": f"Alternative option: {tradeoff}"
    }
    
    session.last_itinerary = itinerary
    
    text = f"Here's a great alternative! 🔄\n\n**{best['name']}**\n\n"
    text += f"📊 Trade-off: {tradeoff}\n\n"
    text += f"💰 ${total_price:.0f} total\n"
    text += f"🛏️ {best['beds']} beds, {best['baths']} baths\n"
    text += f"⭐ {best['rating']}/5 ({best['review_count']} reviews)\n\n"
    text += "Type **BOOK** to reserve!"
    
    return {
        "text": text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": [],
        "quick_replies": ["BOOK", "Show another", "Go back to previous"]
    }

# Import ConversationState enum
from .conversation_flow import ConversationState
