from __future__ import annotations
from typing import Dict, Any
from .conversation_flow import (
    ConversationContext,
    resolve_date_input,
    parse_guest_count,
    ConversationState,
)
from .airbnb_scraper import search_airbnb
from .ranker import rank_listings
from .llm import LLMNotConfiguredError, generate_brand_response

def process_message(message: str, session: Any) -> Dict[str, Any]:
    """
    Enhanced agent with conversation flow
    """
    session.last_user_message = message
    
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
    
    # Update context with new message and auto-complete missing info
    update_context_from_message(context, message)
    auto_complete_missing_slots(context)
    
    # Ready to search immediately
    return execute_search(context, session)

def update_context_from_message(context: ConversationContext, message: str):
    """Extract and update slots from user message"""
    msg = message.lower()
    
    # Capture activity cues early to influence downstream defaults
    activity = context.extract_activity(message)
    if activity:
        context.slots["activity"] = activity
    
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


def auto_complete_missing_slots(context: ConversationContext) -> None:
    """
    Fill in any missing slots so we can always return a recommendation.
    Placeholder for future ML-powered completion.
    """
    # Destination defaults by activity, falls back to a popular choice
    activity_defaults = {
        "beach": "San Diego",
        "ski": "Lake Tahoe",
        "wine": "Napa",
        "hiking": "Big Sur",
        "city": "San Francisco",
        "relaxing": "Carmel",
    }
    
    if not context.slots["destination"]:
        context.slots["destination"] = activity_defaults.get(context.slots.get("activity")) or "San Diego"
    
    if not context.slots["check_in"] or not context.slots["check_out"]:
        check_in, check_out = resolve_date_input("next weekend")
        context.slots["check_in"] = check_in
        context.slots["check_out"] = check_out
    
    if not context.slots["guests"]:
        context.slots["guests"] = 2
    
    context.state = ConversationState.READY_TO_SEARCH

def get_simulated_profile(session: Any) -> Dict[str, Any]:
    """
    Placeholder insights until real historical trip modeling is wired up.
    """
    if not hasattr(session, "profile"):
        session.profile = {
            "avg_budget": 950,
            "travel_party": "two close friends",
            "trip_style": "your signature treat-yourself comfort",
            "signature_move": "picking places with standout reviews",
        }
    return session.profile

def execute_search(context: ConversationContext, session: Any) -> Dict[str, Any]:
    """Execute search and return THE recommendation"""
    
    profile = get_simulated_profile(session)
    
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
            "quick_replies": []
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
    date_label = f"{check_in_date.strftime('%b %d')} – {check_out_date.strftime('%b %d')}"
    activity_context = {
        "beach": "for a breezy beach escape",
        "ski": "for your ski weekend",
        "wine": "for easy vineyard hopping",
        "hiking": "near the trailheads",
        "city": "in the heart of the action",
        "relaxing": "where you can truly unwind",
    }.get(context.slots.get("activity"))
    
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
    headline = f"{context.slots['destination']} · {date_label}"
    lead_in = "Here’s what I’d book"
    if activity_context:
        lead_in += f" {activity_context}"
    lead_in += ":"
    
    upbeat_intro = "That sounds like a blast!"
    if context.slots.get("activity") == "relaxing":
        upbeat_intro = "This is going to feel so restorative!"
    elif context.slots.get("activity") == "ski":
        upbeat_intro = "Fresh powder and good vibes coming right up!"
    elif context.slots.get("activity") == "wine":
        upbeat_intro = "Tasting rooms and sunshine? Say no more!"
    
    persona_line = (
        f"Since you usually budget around ${profile['avg_budget']:.0f} "
        f"and head out with {profile['travel_party']}, we leaned into {profile['trip_style']}."
    )
    
    fallback_lines = [
        upbeat_intro,
        headline,
        "",
        lead_in,
        "",
        f"**{best['name']}**",
        "",
        persona_line,
    ]
    if why_text:
        fallback_lines.extend([why_text, ""])
    fallback_lines.extend(
        [
            f"💰 ${total_price:.0f} total ({nights} nights × ${best['price_per_night']:.0f})",
            f"🛏️ {best['beds']} beds, {best['baths']} baths",
            f"⭐ {best['rating']}/5 ({best['review_count']} reviews)",
            f"✨ {profile['signature_move'].capitalize()}",
            "",
            "Ready when you are—tap the Book button below or tell me what to tweak.",
        ]
    )
    fallback_text = "\n".join(fallback_lines)

    llm_payload = {
        "user_request": getattr(session, "last_user_message", ""),
        "headline": headline,
        "lead_in": lead_in,
        "upbeat_intro": upbeat_intro,
        "persona_line": persona_line,
        "profile": profile,
        "itinerary": {
            "name": best["name"],
            "destination": context.slots["destination"],
            "dates": itinerary["dates"],
            "nights": nights,
            "price_per_night": best["price_per_night"],
            "total_price": total_price,
            "beds": best["beds"],
            "baths": best["baths"],
            "rating": best["rating"],
            "review_count": best["review_count"],
            "amenities": best["amenities"][:6],
            "url": best["url"],
        },
        "why_this_property": why_text,
        "fallback_copy": fallback_text,
    }

    try:
        text = generate_brand_response(llm_payload)
    except LLMNotConfiguredError:
        text = fallback_text

    return {
        "text": text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": [],
        "quick_replies": []
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
            reasons.append(f"Plenty of space for your crew of {context.slots['guests']}")
        else:
            reasons.append("Perfect cozy setup for two")
    
    # Rating
    if property_data["rating"] >= 4.7:
        reasons.append(f"Loved by guests ({property_data['rating']}/5)")
    
    # Budget
    if context.slots.get("budget_max"):
        nights = 2  # Default weekend
        total = property_data["price_per_night"] * nights
        if total <= context.slots["budget_max"]:
            under = context.slots["budget_max"] - total
            reasons.append(f"Under budget (saves you ${under:.0f})")
    
    if not reasons:
        reasons.append("Hand-picked because it's the strongest match available right now")
    
    return " • ".join(reasons[:3])  # Top 3 reasons

def handle_refinement(session: Any, refinement_type: str) -> Dict[str, Any]:
    """Handle user refinement requests"""
    
    context = session.conversation_context
    previous = session.last_itinerary
    profile = get_simulated_profile(session)
    
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
            "quick_replies": []
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
    
    fallback_lines = [
        "Totally hear you—let's try this vibe instead! 🔄",
        "",
        f"**{best['name']}**",
        "",
        f"📊 Trade-off: {tradeoff}",
        f"💡 Keeps things comfy for {profile['travel_party']} without straying from your usual ${profile['avg_budget']:.0f} game plan.",
        "",
        f"💰 ${total_price:.0f} total",
        f"🛏️ {best['beds']} beds, {best['baths']} baths",
        f"⭐ {best['rating']}/5 ({best['review_count']} reviews)",
        "",
        "Tap Book below if this is the one.",
    ]
    fallback_text = "\n".join(fallback_lines)

    llm_payload = {
        "user_request": getattr(session, "last_user_message", ""),
        "refinement_type": refinement_type,
        "profile": profile,
        "tradeoff": tradeoff,
        "itinerary": {
            "name": best["name"],
            "destination": context.slots["destination"],
            "dates": itinerary["dates"],
            "nights": nights,
            "price_per_night": best["price_per_night"],
            "total_price": total_price,
            "beds": best["beds"],
            "baths": best["baths"],
            "rating": best["rating"],
            "review_count": best["review_count"],
            "amenities": best["amenities"][:6],
            "url": best["url"],
        },
        "fallback_copy": fallback_text,
    }

    try:
        text = generate_brand_response(llm_payload)
    except LLMNotConfiguredError:
        text = fallback_text
    
    return {
        "text": text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": [],
        "quick_replies": []
    }
