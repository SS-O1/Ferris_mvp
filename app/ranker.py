from __future__ import annotations
from typing import List, Dict, Any
import math

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Calculate distance between two points in km"""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def rank_listings(listings: List[Dict[str, Any]], intent: Dict[str, Any], origin: str = "SFO") -> List[Dict[str, Any]]:
    """Score and rank listings based on intent"""
    
    AIRPORTS = {
        "SFO": (37.6213, -122.3790),
        "OAK": (37.7126, -122.2197),
        "LAX": (33.9416, -118.4085),
        "SAN": (32.7338, -117.1933),
    }
    
    origin_coords = AIRPORTS.get(origin.upper(), AIRPORTS["SFO"])
    
    scored = []
    for listing in listings:
        score = 100.0
        
        nights = intent.get("nights") or 2
        price_per_night = listing.get("price_per_night") or 0
        total_price = price_per_night * nights
        
        # Budget fit
        if intent.get("budget_max"):
            if total_price > intent["budget_max"]:
                score -= min(50, (total_price - intent["budget_max"]) / 20)
            else:
                score += (intent["budget_max"] - total_price) / 50
        
        # Guest capacity
        if listing["guests_max"] < intent.get("guests", 2):
            continue
        
        # Rating boost
        rating = listing.get("rating") or 0
        review_count = listing.get("review_count") or 0
        score += (rating - 4.0) * 10
        score += min(10, review_count / 10)
        
        # Distance preference
        dist_km = haversine(
            origin_coords[0], origin_coords[1],
            listing["coords"][0], listing["coords"][1]
        )
        if dist_km < 200:
            score += 10
        elif dist_km > 800:
            score -= 5
        
        # Beds/baths quality
        score += (listing.get("beds") or 0) * 2
        score += (listing.get("baths") or 0) * 3
        
        scored.append({
            "score": score,
            "total_price": total_price,
            "listing": listing
        })
    
    scored.sort(key=lambda x: (-x["score"], x["total_price"]))
    
    return [item["listing"] for item in scored]
