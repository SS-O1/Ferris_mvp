from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from .conversation_flow import (
    ConversationContext,
    generate_clarification,
    resolve_date_input,
    parse_guest_count,
    ConversationState,
)
from .airbnb_scraper import search_airbnb
from .ranker import rank_listings
from .llm import LLMNotConfiguredError, generate_brand_response


def process_message(message: str, session: Any) -> Dict[str, Any]:
    """
    Production-ready agent with intelligent conversation flow
    Features:
    - Step-by-step clarification questions
    - Smart refinement handling (cheaper, bigger, smaller, different)
    - Fuzzy date parsing with spelling correction
    - Natural language understanding
    - Beautiful LLM-powered responses with fallbacks
    """
    session.last_user_message = message
    
    # Initialize conversation context
    if not hasattr(session, 'conversation_context'):
        session.conversation_context = ConversationContext()
    
    context = session.conversation_context
    msg_lower = message.lower().strip()
    
    # Handle refinement requests (when user wants to tweak the recommendation)
    if context.state.value == "showing_result" and hasattr(session, 'last_itinerary'):
        
        # Price refinements
        if any(word in msg_lower for word in ["cheaper", "budget", "less expensive", "too expensive", "lower price", "save money"]):
            return handle_refinement(session, "cheaper")
        
        # Size refinements - BIGGER
        elif any(word in msg_lower for word in ["bigger", "more beds", "more space", "more room", "larger", "spacious"]):
            return handle_refinement(session, "bigger")
        
        # Size refinements - SMALLER (NEW!)
        elif any(word in msg_lower for word in ["smaller", "fewer beds", "less space", "only need", "just need", "don't need", "too big", "right size"]):
            return handle_refinement(session, "smaller")
        
        # Different location/property
        elif any(word in msg_lower for word in ["different", "something else", "another", "other option", "show me more", "not this one"]):
            return handle_refinement(session, "different")
    
    # Update context from user message
    update_context_from_message(context, message)
    
    # Check if we need to ask clarifying questions
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
    
    # All info collected - execute search!
    return execute_search(context, session)


def update_context_from_message(context: ConversationContext, message: str):
    """
    Enhanced slot extraction with fuzzy matching and natural language understanding
    """
    msg = message.lower().strip()
    
    # Extract activity/intent early (hiking, beach, skiing, etc.)
    activity = context.extract_activity(message)
    if activity:
        context.slots["activity"] = activity
    
    # Handle custom date input with fuzzy parsing
    if context.waiting_for_custom_dates or (not context.slots["check_in"] and any(char.isdigit() for char in msg)):
        looks_like_date = any(month in msg for month in [
            "jan", "feb", "mar", "apr", "may", "jun", 
            "jul", "aug", "sep", "oct", "nov", "dec"
        ]) or "/" in msg or "-" in msg
        
        if looks_like_date:
            context.waiting_for_custom_dates = False
            try:
                check_in, check_out = resolve_date_input(message)
                context.slots["check_in"] = check_in
                context.slots["check_out"] = check_out
                return
            except Exception as e:
                print(f"Date parsing failed: {e}")
                # Continue to other parsing
    
    # Comprehensive destination extraction
    destinations = [
        "san diego", "lake tahoe", "tahoe", "napa", "big sur", "santa cruz",
        "malibu", "monterey", "yosemite", "mammoth", "joshua tree", "sonoma",
        "san francisco", "los angeles", "santa barbara", "carmel", "mendocino",
        "ojai", "healdsburg", "paso robles", "sequoia", "oakland", "tahoe city", 
        "big bear", "palm springs", "santa monica", "laguna beach", "half moon bay"
    ]
    
    for dest in destinations:
        if dest in msg:
            # Normalize destination names
            if dest == "tahoe" or dest == "tahoe city":
                context.slots["destination"] = "Lake Tahoe"
            elif dest == "sf" or dest == "san francisco":
                context.slots["destination"] = "San Francisco"
            elif dest == "la" or dest == "los angeles":
                context.slots["destination"] = "Los Angeles"
            else:
                context.slots["destination"] = dest.title()
            break
    
    # Date keywords (this weekend, next weekend, etc.)
    if any(word in msg for word in ["this weekend", "next weekend", "weekend", "flexible"]):
        check_in, check_out = resolve_date_input(message)
        context.slots["check_in"] = check_in
        context.slots["check_out"] = check_out
    
    # Guest count extraction - ENHANCED
    # Check for keywords first
    if any(word in msg for word in ["people", "guests", "person", "just me", "solo", "couple", "group", "family", "adults", "friends"]):
        context.slots["guests"] = parse_guest_count(message)
    
    # Check for numbers with keywords (e.g., "5 people")
    if context.slots["guests"] is None:
        numbers = re.findall(r'\b(\d+)\s*(?:people|guests|adults|persons?|friends?)\b', msg)
        if numbers:
            context.slots["guests"] = int(numbers[0])
    
    # Check for standalone numbers (when asked "how many people?", user just says "5")
    if context.slots["guests"] is None and msg.strip().isdigit():
        context.slots["guests"] = int(msg.strip())
    
    # Budget extraction
    budget_match = re.search(r'under\s*\$?(\d+)', msg)
    if budget_match:
        context.slots["budget_max"] = float(budget_match.group(1))
    
    budget_match2 = re.search(r'budget\s*\$?(\d+)', msg)
    if budget_match2:
        context.slots["budget_max"] = float(budget_match2.group(1))


def get_simulated_profile(session: Any) -> Dict[str, Any]:
    """
    Simulated user profile for personalized messaging
    In production, this would pull from user's trip history
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
    """
    Execute Airbnb search and return THE best recommendation
    Uses Logan's beautiful personality + your smart logic
    """
    profile = get_simulated_profile(session)
    
    # Search Airbnb
    listings = search_airbnb(
        destination=context.slots["destination"],
        check_in=context.slots["check_in"],
        check_out=context.slots["check_out"],
        guests=context.slots["guests"]
    )
    
    # Handle no results
    if not listings:
        return {
            "text": f"Hmm, I couldn't find available places in {context.slots['destination']} for those dates. Want to try different dates or another destination?",
            "itinerary": None,
            "state": "FAILED",
            "needed": [],
            "quick_replies": ["This weekend", "Next weekend", "Different location"]
        }
    
    # Rank listings and get THE best one
    origin = getattr(session, 'origin', 'SFO') if hasattr(session, 'origin') else "SFO"
    
    intent = {
        "destination": context.slots["destination"],
        "check_in": context.slots["check_in"],
        "check_out": context.slots["check_out"],
        "guests": context.slots["guests"],
        "budget_max": context.slots.get("budget_max")
    }
    
    ranked = rank_listings(listings, intent, origin)
    best = ranked[0]
    
    # Mark as shown (for refinements)
    context.shown_properties.append(best["id"])
    context.state = ConversationState.SHOWING_RESULT
    
    # Calculate pricing
    check_in_date = datetime.fromisoformat(context.slots["check_in"])
    check_out_date = datetime.fromisoformat(context.slots["check_out"])
    nights = (check_out_date - check_in_date).days
    total_price = best["price_per_night"] * nights
    date_label = f"{check_in_date.strftime('%b %d')} – {check_out_date.strftime('%b %d')}"
    
    # Activity-based context
    activity_context = {
        "beach": "for a breezy beach escape",
        "ski": "for your ski weekend",
        "wine": "for easy vineyard hopping",
        "hiking": "near the trailheads",
        "city": "in the heart of the action",
        "relaxing": "where you can truly unwind",
    }.get(context.slots.get("activity"))
    
    # Build itinerary object
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
        "why_this_property": generate_recommendation_reason(best, context, profile)
    }
    
    session.last_itinerary = itinerary
    
    # Build beautiful response with personality
    why_text = itinerary["why_this_property"]
    headline = f"{context.slots['destination']} · {date_label}"
    lead_in = "Here's what I'd book"
    if activity_context:
        lead_in += f" {activity_context}"
    lead_in += ":"
    
    # Dynamic intro based on activity
    upbeat_intro = "That sounds like a blast!"
    if context.slots.get("activity") == "relaxing":
        upbeat_intro = "This is going to feel so restorative!"
    elif context.slots.get("activity") == "ski":
        upbeat_intro = "Fresh powder and good vibes coming right up!"
    elif context.slots.get("activity") == "wine":
        upbeat_intro = "Tasting rooms and sunshine? Say no more!"
    elif context.slots.get("activity") == "hiking":
        upbeat_intro = "Trail time! You're going to love this."
    
    persona_line = (
        f"Since you usually budget around ${profile['avg_budget']:.0f} "
        f"and head out with {profile['travel_party']}, we leaned into {profile['trip_style']}."
    )
    
    # Fallback text (used if LLM not configured)
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
    
    fallback_lines.extend([
        f"💰 ${total_price:.0f} total ({nights} nights × ${best['price_per_night']:.0f})",
        f"🛏️ {best['beds']} beds, {best['baths']} baths",
        f"⭐ {best['rating']}/5 ({best['review_count']} reviews)",
        f"✨ {profile['signature_move'].capitalize()}",
        "",
        "Ready when you are—tap the Book button below or tell me what to tweak.",
    ])
    fallback_text = "\n".join(fallback_lines)

    # Try to use LLM for natural language generation
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


def generate_recommendation_reason(property_data: Dict, context: ConversationContext, profile: Dict) -> str:
    """
    Generate personalized 'why this property' reasoning
    """
    reasons = []
    
    # Location highlight
    if property_data.get("coords"):
        reasons.append(f"Prime location in {context.slots['destination']}")
    
    # Capacity matching
    if property_data["guests_max"] >= context.slots["guests"]:
        if context.slots["guests"] > 2:
            reasons.append(f"Plenty of space for your crew of {context.slots['guests']}")
        else:
            reasons.append(f"Perfect cozy setup for two")
    
    # Rating highlight
    if property_data["rating"] >= 4.7:
        reasons.append(f"Loved by guests ({property_data['rating']}/5)")
    
    # Budget alignment
    if context.slots.get("budget_max"):
        nights = 2
        total = property_data["price_per_night"] * nights
        if total <= context.slots["budget_max"]:
            under = context.slots["budget_max"] - total
            reasons.append(f"Under budget (saves you ${under:.0f})")
    
    if not reasons:
        reasons.append("Hand-picked as the strongest match right now")
    
    return " • ".join(reasons[:3])


def handle_refinement(session: Any, refinement_type: str) -> Dict[str, Any]:
    """
    Enhanced refinement handler with smart filtering
    Supports: cheaper, bigger, smaller, different
    """
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
    
    # Filter out already shown properties
    available = [l for l in listings if l["id"] not in context.shown_properties]
    
    if not available:
        return {
            "text": "That's all I have for those criteria. Want to try different dates or a different location?",
            "itinerary": previous,
            "state": "AWAITING_CONSENT",
            "needed": [],
            "quick_replies": ["Different dates", "Different location", "Book this one"]
        }
    
    # Apply refinement filter
    if refinement_type == "cheaper":
        available.sort(key=lambda x: x["price_per_night"])
        best = available[0]
        nights = previous["nights"]
        savings = previous['total_price'] - (best['price_per_night'] * nights)
        tradeoff = f"${savings:.0f} cheaper"
    
    elif refinement_type == "bigger":
        available.sort(key=lambda x: x["beds"], reverse=True)
        best = available[0]
        tradeoff = f"{best['beds']} beds (vs {previous['stay']['beds']})"
    
    elif refinement_type == "smaller":
        # Filter for properties with fewer beds
        smaller_props = [p for p in available if p["beds"] < previous['stay']['beds']]
        
        if not smaller_props:
            # No smaller available - get cheapest instead
            available.sort(key=lambda x: x["price_per_night"])
            best = available[0]
            tradeoff = "Closest match available (still great!)"
        else:
            # Sort by fewest beds, but prioritize good ratings
            smaller_props.sort(key=lambda x: (x["beds"], -x["rating"]))
            best = smaller_props[0]
            bed_diff = previous['stay']['beds'] - best['beds']
            tradeoff = f"{best['beds']} beds (right-sized, down {bed_diff} from before)"
    
    else:  # different
        best = available[0]
        tradeoff = "Different vibe and location"
    
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
        "why_this_property": f"Refined option: {tradeoff}"
    }
    
    session.last_itinerary = itinerary
    
    # Personalized response based on refinement type
    if refinement_type == "smaller":
        intro = f"Perfect! Let's right-size this for you. 🎯"
    elif refinement_type == "cheaper":
        intro = f"Totally hear you—let's save you some cash! 💰"
    elif refinement_type == "bigger":
        intro = f"More space coming right up! 🏡"
    else:
        intro = f"Let's try a different vibe! 🔄"
    
    fallback_text = (
        f"{intro}\n\n"
        f"**{best['name']}**\n\n"
        f"📊 {tradeoff}\n\n"
        f"💰 ${total_price:.0f} total\n"
        f"🛏️ {best['beds']} beds, {best['baths']} baths\n"
        f"⭐ {best['rating']}/5 ({best['review_count']} reviews)\n\n"
        f"Tap Book if this is the one, or keep tweaking!"
    )
    
    return {
        "text": fallback_text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": [],
        "quick_replies": ["BOOK", "Show another", "Too expensive"]
    }
