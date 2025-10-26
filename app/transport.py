from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent

_ROUTES_STATIC: Dict[Tuple[str, str], List[Dict[str, str]]] = {
    (
        "Berkeley, CA",
        "Lake Tahoe",
    ): [
        {
            "label": "Drive via I-80 E",
            "mode": "car",
            "duration": "3 hr 30 min",
            "distance": "186 miles",
            "cost": "≈ $55 gas + $7 bridge toll",
            "highlights": "Fastest door-to-door option with scenic summit views.",
        },
        {
            "label": "Amtrak Capitol Corridor + Tahoe Shuttle",
            "mode": "train_bus",
            "duration": "4 hr 15 min",
            "distance": "Rail to Truckee, shuttle to Tahoe",
            "cost": "$48 saver fare",
            "highlights": "Wi-Fi on the train, skip driving in snow.",
        },
        {
            "label": "Lux Coach to Heavenly Village",
            "mode": "bus",
            "duration": "4 hr 40 min",
            "distance": "Door-to-door charter",
            "cost": "$79 round-trip",
            "highlights": "Includes snacks and gear storage; relax the entire way.",
        },
    ]
}

_TRANSPORT_CACHE: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
_TRANSPORT_LOADED = False


def get_transportation_options(origin: str, destination: str) -> List[Dict[str, str]]:
    _ensure_transport_loaded()

    origin_lower = origin.lower()
    destination_lower = destination.lower()

    for key, options in _TRANSPORT_CACHE.items():
        key_origin, key_dest = key
        if key_origin.lower() == origin_lower and (
            key_dest.lower() in destination_lower or destination_lower in key_dest.lower()
        ):
            return options

    for key, options in _TRANSPORT_CACHE.items():
        key_origin, key_dest = key
        if key_dest.lower() in destination_lower or destination_lower in key_dest.lower():
            return options

    for key, options in _ROUTES_STATIC.items():
        key_origin, key_dest = key
        if key_origin.lower() == origin_lower and key_dest.lower() in destination_lower:
            return options

    generic_key = (origin, destination.split(" ·")[0]) if " ·" in destination else None
    if generic_key and generic_key in _ROUTES_STATIC:
        return _ROUTES_STATIC[generic_key]

    return []


def _ensure_transport_loaded() -> None:
    global _TRANSPORT_LOADED
    if _TRANSPORT_LOADED:
        return
    _load_transport_catalog("transport.json")
    _TRANSPORT_LOADED = True


def _load_transport_catalog(filename: str) -> None:
    data_path = DATA_DIR / filename
    if not data_path.exists():
        return

    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    overview = raw.get("trip_overview", {})
    origin = overview.get("departure_city")
    destination = overview.get("destination")
    if not origin or not destination:
        return

    options: List[Dict[str, str]] = []

    flight_options = raw.get("flight_options", {}).get("outbound_flights", [])
    flight_pick = _select_recommended(flight_options)
    if flight_pick:
        baggage = flight_pick.get("baggage", {})
        highlights_parts = []
        if flight_pick.get("notes"):
            highlights_parts.append(flight_pick["notes"])
        if baggage:
            checked = baggage.get("checked")
            if checked:
                highlights_parts.append(f"Checked bags: {checked}")
        highlights = " / ".join(highlights_parts) if highlights_parts else "Fastest air option."
        options.append(
            {
                "label": f"{flight_pick.get('airline', 'Flight')} {flight_pick.get('route', '')}".strip(),
                "mode": "flight",
                "duration": flight_pick.get("duration", ""),
                "cost": _format_cost(flight_pick.get("price_total")),
                "highlights": highlights,
            }
        )

    to_airport = raw.get("berkeley_to_airport", {})
    bay_area_leg = _select_recommended(
        to_airport.get("to_oakland_airport", []),
        default=_select_recommended(to_airport.get("to_san_francisco_airport", [])),
    )
    if bay_area_leg:
        cost = bay_area_leg.get("total_cost") or bay_area_leg.get("cost_per_person")
        notes = bay_area_leg.get("instructions") or bay_area_leg.get("notes", "Direct to the terminal.")
        options.append(
            {
                "label": f"{bay_area_leg.get('type', 'Ground transfer')} to the airport",
                "mode": "ground",
                "duration": bay_area_leg.get("duration", ""),
                "cost": _format_cost(cost),
                "highlights": notes,
            }
        )

    arrival_leg_data = raw.get("cancun_airport_to_hotels", {})
    arrival_leg = _select_recommended(arrival_leg_data.values())
    if arrival_leg:
        cost = arrival_leg.get("cost_roundtrip") or arrival_leg.get("cost_per_person_roundtrip")
        notes = arrival_leg.get("notes") or arrival_leg.get("advance_booking", "Pre-book recommended.")
        options.append(
            {
                "label": f"{arrival_leg.get('provider', 'Transfer')} to the resort",
                "mode": "ground",
                "duration": arrival_leg.get("duration", ""),
                "cost": _format_cost(cost),
                "highlights": notes,
            }
        )

    if options:
        origin_keys = {origin, origin.replace("California", "CA"), origin.replace(", California", ", CA")}
        destination_keys = {
            destination,
            destination.split(",")[0],
            destination.replace("Mexico", "MX"),
        }
        origin_keys = {key.strip() for key in origin_keys if key}
        destination_keys = {key.strip() for key in destination_keys if key}

        for ok in origin_keys:
            for dk in destination_keys:
                _TRANSPORT_CACHE[(ok, dk)] = options


def _select_recommended(entries, default=None):
    if not entries:
        return default
    if isinstance(entries, dict):
        entries = list(entries.values())
    elif not isinstance(entries, (list, tuple)):
        entries = list(entries)
    if not entries:
        return default
    for item in entries:
        if isinstance(item, dict) and item.get("recommended"):
            return item
    return entries[0] if entries else default


def _format_cost(value) -> str:
    if value is None:
        return "See details"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    if amount.is_integer():
        amount = int(amount)
    return f"${amount}"
