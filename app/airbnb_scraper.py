from __future__ import annotations
import requests
import random
from typing import List, Dict, Any

def search_airbnb(destination: str, check_in: str, check_out: str, guests: int = 2) -> List[Dict[str, Any]]:
    """Search Airbnb listings - uses mock data for reliable demo"""
    return _generate_mock_listings(destination, check_in, check_out, guests)

def _generate_mock_listings(destination: str, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
    """Generate realistic mock Airbnb data"""
    
    coords_map = {
        "tahoe": (39.0968, -120.0324),
        "lake tahoe": (39.0968, -120.0324),
        "south lake tahoe": (38.9399, -119.9772),
        "san diego": (32.7157, -117.1611),
        "napa": (38.2975, -122.2869),
        "big sur": (36.2704, -121.8081),
        "joshua tree": (34.1347, -116.3128),
        "palm springs": (33.8303, -116.5453),
        "santa barbara": (34.4208, -119.6982),
        "monterey": (36.6002, -121.8947),
        "san francisco": (37.7749, -122.4194),
        "los angeles": (34.0522, -118.2437),
    }
    
    dest_lower = destination.lower()
    coords = coords_map.get(dest_lower, (37.7749, -122.4194))
    
    templates = [
        {"name": "Modern Cabin with Mountain Views", "beds": 2, "baths": 1.5, "base_price": 180},
        {"name": "Luxury Condo Downtown", "beds": 3, "baths": 2, "base_price": 250},
        {"name": "Cozy Studio Near Beach", "beds": 1, "baths": 1, "base_price": 120},
        {"name": "Spacious Home with Hot Tub", "beds": 4, "baths": 2.5, "base_price": 320},
        {"name": "Charming Cottage with Fireplace", "beds": 2, "baths": 1, "base_price": 150},
        {"name": "Beachfront Apartment", "beds": 2, "baths": 2, "base_price": 280},
        {"name": "Rustic Retreat with Deck", "beds": 3, "baths": 1.5, "base_price": 200},
        {"name": "Chic Loft in Arts District", "beds": 1, "baths": 1, "base_price": 140},
        {"name": "Family House Near Attractions", "beds": 4, "baths": 3, "base_price": 350},
        {"name": "Vintage Bungalow with Garden", "beds": 2, "baths": 1, "base_price": 165},
    ]
    
    listings = []
    for i, template in enumerate(templates):
        lat_offset = random.uniform(-0.05, 0.05)
        lng_offset = random.uniform(-0.05, 0.05)
        price_variance = random.randint(-20, 40)
        
        listings.append({
            "id": f"MOCK_{destination.replace(' ', '_').upper()}_{i+1}",
            "name": template["name"],
            "destination": destination,
            "coords": (coords[0] + lat_offset, coords[1] + lng_offset),
            "beds": template["beds"],
            "baths": template["baths"],
            "guests_max": template["beds"] * 2,
            "price_per_night": template["base_price"] + price_variance,
            "rating": round(random.uniform(4.2, 4.95), 2),
            "review_count": random.randint(15, 250),
            "image_url": f"https://placehold.co/400x300/667eea/ffffff?text={template['name'].split()[0]}",
            "url": f"https://airbnb.com/rooms/{random.randint(10000000, 99999999)}",
            "amenities": random.sample(["Wifi", "Kitchen", "Free parking", "Pool", "Hot tub", "AC", "Washer", "Workspace"], k=random.randint(3, 6)),
            "cancellation_policy": random.choice(["Flexible", "Moderate", "Strict"])
        })
    
    return listings
