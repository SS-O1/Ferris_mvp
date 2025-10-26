from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent

_CATALOG_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_CATALOG_LOADED = False

_DESTINATION_COORDS: Dict[str, tuple[float, float]] = {
    "lake tahoe": (39.0968, -120.0324),
    "tahoe city": (39.1720, -120.1380),
    "south lake tahoe": (38.9399, -119.9772),
    "cancun": (21.1619, -86.8515),
    "cancun mexico": (21.1619, -86.8515),
}
_DEFAULT_COORDS = (37.7749, -122.4194)


def search_airbnb(destination: str, check_in: str, check_out: str, guests: int = 2) -> List[Dict[str, Any]]:
    """Return curated listings when the catalog contains them, else fallback to mocks."""
    _ensure_catalog_loaded()

    catalog_listings = _match_catalog(destination)
    if catalog_listings:
        listings_copy = copy.deepcopy(catalog_listings)
        return _filter_guest_capacity(listings_copy, guests)

    return _generate_mock_listings(destination, check_in, check_out, guests)


def _ensure_catalog_loaded() -> None:
    global _CATALOG_LOADED
    if _CATALOG_LOADED:
        return
    _load_catalog_file("accom.json")
    _CATALOG_LOADED = True


def _load_catalog_file(filename: str) -> None:
    data_path = DATA_DIR / filename
    if not data_path.exists():
        return

    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    destinations = raw.get("travel_database", {}).get("destinations", [])
    for dest_entry in destinations:
        listings = _convert_destination_entry(dest_entry)
        if not listings:
            continue
        for key in _destination_keys(dest_entry):
            _CATALOG_CACHE[key] = listings


def _destination_keys(dest_entry: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    name = dest_entry.get("name", "")
    region = dest_entry.get("region", "")
    dest_id = dest_entry.get("destination_id")

    for value in (name, region):
        if value:
            keys.append(_normalize_key(value))
            primary = value.split(",")[0]
            keys.append(_normalize_key(primary))
    if dest_id:
        keys.append(dest_id.lower())

    return [key for key in {k for k in keys if k}]


def _normalize_key(value: str) -> str:
    return value.strip().lower()


def _match_catalog(destination: str) -> List[Dict[str, Any]]:
    dest_lower = destination.lower()
    if dest_lower in _CATALOG_CACHE:
        return _CATALOG_CACHE[dest_lower]

    for key, listings in _CATALOG_CACHE.items():
        if key in dest_lower or dest_lower in key:
            return listings

    return []


def _convert_destination_entry(dest_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_coords = _resolve_coords(dest_entry.get("name", ""))
    listings: List[Dict[str, Any]] = []

    for prop in dest_entry.get("properties", []):
        normalized = _normalize_catalog_property(dest_entry, prop, base_coords)
        if normalized:
            listings.append(normalized)

    return listings


def _normalize_catalog_property(
    dest_entry: Dict[str, Any],
    prop: Dict[str, Any],
    base_coords: tuple[float, float],
) -> Optional[Dict[str, Any]]:
    name = prop.get("name") or prop.get("title")
    if not name:
        return None

    listing_id = prop.get("listing_id") or prop.get("property_id") or name.lower().replace(" ", "-")

    coords = (
        base_coords[0] + random.uniform(-0.02, 0.02),
        base_coords[1] + random.uniform(-0.02, 0.02),
    )

    pricing = prop.get("pricing", {})
    trip_info = dest_entry.get("trip_overview") or dest_entry.get("search_info") or {}
    num_nights = pricing.get("num_nights") or trip_info.get("num_nights") or 1
    price_per_night = pricing.get("nightly_rate")
    total_price = pricing.get("total_cost_usd")
    if price_per_night is None and total_price:
        price_per_night = round(total_price / max(num_nights, 1))
    if total_price is None and price_per_night:
        total_price = price_per_night * max(num_nights, 1)

    property_details = prop.get("property_details", {})
    accommodation = prop.get("accommodation", {})
    ratings = prop.get("ratings", {})

    rating = prop.get("rating") or property_details.get("rating") or ratings.get("overall")
    review_count = (
        prop.get("num_reviews")
        or property_details.get("num_reviews")
        or ratings.get("num_reviews")
    )

    beds = (
        prop.get("beds")
        or property_details.get("beds")
        or property_details.get("bedrooms")
        or accommodation.get("bed_configuration")
        or prop.get("bedrooms")
    )
    beds = _extract_numeric(beds, fallback=3)

    baths = (
        prop.get("bathrooms")
        or property_details.get("bathrooms")
        or accommodation.get("bathrooms")
    )
    baths = _extract_numeric(baths, fallback=2)

    guests_max = (
        prop.get("max_guests")
        or property_details.get("max_guests")
        or accommodation.get("max_occupancy")
        or trip_info.get("num_adults")
        or 4
    )
    guests_max = _extract_numeric(guests_max, fallback=4)

    amenities = (
        prop.get("amenities")
        or property_details.get("amenities")
        or accommodation.get("amenities")
        or []
    )
    if isinstance(amenities, str):
        amenities = [amenities]

    tags = prop.get("tags") or {}
    vibe = _derive_vibe_tags(tags, amenities, prop.get("property_type", ""), dest_entry.get("name", ""))

    description = prop.get("description")
    if not description:
        description = _compose_description(prop, amenities, tags)

    image_url = prop.get(
        "image_url",
        f"https://source.unsplash.com/featured/?{_normalize_key(dest_entry.get('name', '').split(',')[0])},travel,{random.randint(100, 999)}",
    )

    return {
        "id": f"CATALOG_{listing_id}",
        "name": name,
        "destination": dest_entry.get("name") or destination_fallback(dest_entry),
        "coords": coords,
        "beds": beds,
        "baths": baths,
        "guests_max": guests_max,
        "price_per_night": price_per_night,
        "total_price": total_price,
        "rating": rating,
        "review_count": review_count,
        "image_url": image_url,
        "url": prop.get("url"),
        "amenities": amenities[:12] if isinstance(amenities, list) else amenities,
        "cancellation_policy": prop.get("cancellation_policy", "Flexible"),
        "description": description,
        "vibe": vibe,
    }


def destination_fallback(dest_entry: Dict[str, Any]) -> str:
    return dest_entry.get("region") or dest_entry.get("name", "Curated Destination")


def _extract_numeric(value: Any, fallback: int | float | None = None) -> Optional[float]:
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        if digits:
            try:
                number = float(digits)
                if number.is_integer():
                    return int(number)
                return number
            except ValueError:
                return fallback
    return fallback


def _derive_vibe_tags(
    tags: Dict[str, Any],
    amenities: List[str],
    property_type: str,
    destination_name: str,
) -> List[str]:
    result: List[str] = []
    amenities_text = " ".join(amenities).lower()
    property_type_lower = (property_type or "").lower()

    if isinstance(tags, dict):
        if tags.get("all_inclusive"):
            result.append("all-inclusive energy")
        if tags.get("adults_only"):
            result.append("adults-only vibe")
        if tags.get("eco_certified"):
            result.append("eco-certified stay")

    if "spa" in amenities_text or "wellness" in amenities_text:
        result.append("spa & wellness")
    if "pool" in amenities_text or "infinity" in amenities_text:
        result.append("poolside scene")
    if "beach" in amenities_text or "ocean" in amenities_text or "shore" in amenities_text:
        result.append("beach access")
    if "fireplace" in amenities_text:
        result.append("fireside evenings")
    if "ski" in amenities_text or "heavenly" in amenities_text or "northstar" in amenities_text:
        result.append("slope-ready")
    if "resort" in property_type_lower:
        result.append("resort living")

    if not result:
        result.append(f"{destination_name.split(',')[0]} favorite".strip())

    return result[:3]


def _compose_description(prop: Dict[str, Any], amenities: List[str], tags: Dict[str, Any]) -> str:
    segments: List[str] = []
    property_type = prop.get("property_type")
    if property_type:
        segments.append(property_type)
    if isinstance(tags, dict):
        if tags.get("all_inclusive"):
            segments.append("All-inclusive perks")
        if tags.get("adults_only"):
            segments.append("Adults-only atmosphere")

    highlights = amenities[:3] if isinstance(amenities, list) else []
    if highlights:
        segments.append("Highlights: " + ", ".join(highlights))

    return ". ".join(segments).strip()


def _resolve_coords(destination_name: str) -> tuple[float, float]:
    key = _normalize_key(destination_name.split(",")[0]) if destination_name else ""
    if key in _DESTINATION_COORDS:
        return _DESTINATION_COORDS[key]

    return _DESTINATION_COORDS.get(_normalize_key(destination_name), _DEFAULT_COORDS)


def _filter_guest_capacity(listings: List[Dict[str, Any]], guests: int) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for listing in listings:
        capacity = _extract_numeric(listing.get("guests_max"), fallback=None)
        if capacity is None or capacity >= guests:
            if capacity is None:
                listing["guests_max"] = guests
            filtered.append(listing)
    return filtered or listings


def _generate_mock_listings(destination: str, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
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
        "cancun": (21.1619, -86.8515),
    }

    dest_lower = destination.lower()
    coords = coords_map.get(dest_lower, _DEFAULT_COORDS)

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

    listings: List[Dict[str, Any]] = []
    for i, template in enumerate(templates):
        lat_offset = random.uniform(-0.05, 0.05)
        lng_offset = random.uniform(-0.05, 0.05)
        price_variance = random.randint(-20, 40)

        listings.append(
            {
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
                "image_url": f"https://via.placeholder.com/400x300/667eea/ffffff?text={template['name'].split()[0]}",
                "url": f"https://airbnb.com/rooms/{random.randint(10000000, 99999999)}",
                "amenities": random.sample(
                    ["Wifi", "Kitchen", "Free parking", "Pool", "Hot tub", "AC", "Washer", "Workspace"],
                    k=random.randint(3, 6),
                ),
                "cancellation_policy": random.choice(["Flexible", "Moderate", "Strict"]),
                "description": "",
                "vibe": ["curated escape"],
            }
        )

    return listings
