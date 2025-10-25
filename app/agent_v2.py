from __future__ import annotations
from typing import Dict, Any
from .intent_parser import parse_intent
from .airbnb_scraper import search_airbnb
from .ranker import rank_listings

def process_message(message: str, session: Any) -> Dict[str, Any]:
    """Main agent: parse intent → search → rank → return best"""
    
    intent = parse_intent(message)
    
    if not intent["destination"]:
        return {
            "text": "Where would you like to go? Try: 'beach weekend in San Diego' or 'skiing in Tahoe'",
            "itinerary": None,
            "state": "COLLECTING_SLOTS",
            "needed": ["destination"]
        }
    
    listings = search_airbnb(
        destination=intent["destination"],
        check_in=intent["check_in"],
        check_out=intent["check_out"],
        guests=intent["guests"]
    )
    
    if not listings:
        return {
            "text": f"I couldn't find any places in {intent['destination']}. Try a different destination?",
            "itinerary": None,
            "state": "FAILED",
            "needed": []
        }
    
    origin = getattr(session.slots, 'origin', 'SFO') or "SFO"
    ranked = rank_listings(listings, intent, origin)
    best = ranked[0]
    
    nights = 2
    total_price = best["price_per_night"] * nights
    
    itinerary = {
        "id": best["id"],
        "destination": intent["destination"],
        "name": best["name"],
        "dates": {
            "check_in": intent["check_in"],
            "check_out": intent["check_out"]
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
            "cancellation_policy": best["cancellation_policy"]
        },
        "total_price": total_price,
        "currency": "USD"
    }
    
    session.last_itinerary = itinerary
    session.state = "AWAITING_CONSENT"
    
    text = f"Found the perfect spot: **{best['name']}** in {intent['destination']}!\n\n"
    text += f"💰 ${total_price:.0f} total ({nights} nights × ${best['price_per_night']:.0f})\n"
    text += f"🛏️ {best['beds']} beds, {best['baths']} baths\n"
    text += f"⭐ {best['rating']}/5 ({best['review_count']} reviews)\n\n"
    text += f"Type **BOOK** to reserve!"
    
    return {
        "text": text,
        "itinerary": itinerary,
        "state": "AWAITING_CONSENT",
        "needed": []
    }
