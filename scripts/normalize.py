#!/usr/bin/env python3
"""
Shared normalization utilities for Apify Google Flights data.
Actor: johnvc~google-flights-data-scraper (ID: 1dYHRKkEBHBPd0JM7)
"""

# ── Unified Flight Schema ─────────────────────────────────────────────────────
# {
#   "id": str,                   # "apify_{flight_number}_{departure_time}"
#   "source": "apify_google",
#   "is_best": bool,             # True if in best_flights list
#   "airlines": [str],           # e.g. ["Bamboo Airways"]
#   "flight_numbers": [str],     # e.g. ["QH 208"]
#   "origin": str,               # IATA "SGN"
#   "destination": str,          # IATA "HAN"
#   "departure": str,            # "2026-06-20 08:40"
#   "arrival": str,              # "2026-06-20 10:50"
#   "duration_minutes": int,     # 130
#   "stops": int,                # 0, 1, 2...
#   "stop_airports": [str],      # IATA codes of transit airports
#   "cabin_class": str,          # "ECONOMY"
#   "price_total": float,        # 163.0
#   "price_currency": str,       # "USD"
#   "price_breakdown": {...},
#   "segments": [dict],          # raw leg objects
#   "booking_token": str|None,   # departure_token
#   "booking_url": None,         # Google Flights doesn't provide direct URL
#   "airplane": str|None,        # "Airbus A321"
#   "legroom": str|None,         # "29 in"
#   "often_delayed": bool,
#   "carbon_g": int,             # carbon emissions in grams
#   "raw": dict,
# }
# ─────────────────────────────────────────────────────────────────────────────


def extract_all_flights(apify_items):
    """
    Extract individual flight itineraries from Apify response.

    Apify returns 1 item (top-level object) containing:
      - best_flights: [flight_obj, ...]
      - other_flights: [flight_obj, ...]

    Returns: list of normalized flight dicts.
    """
    if not apify_items:
        return []

    results = []
    item = apify_items[0] if isinstance(apify_items, list) else apify_items

    for flight in item.get("best_flights", []):
        results.append(normalize_apify_itinerary(flight, is_best=True))

    for flight in item.get("other_flights", []):
        results.append(normalize_apify_itinerary(flight, is_best=False))

    return results


def normalize_apify_itinerary(flight, is_best=False):
    """
    Normalize a single flight object from best_flights / other_flights.

    Structure of 'flight':
      {
        "flights": [ {leg}, {leg}, ... ],   # list of legs
        "total_duration": 130,              # total minutes
        "price": 163,
        "type": "Round trip",
        "departure_token": "...",
        "carbon_emissions": {"this_flight": 136000, ...}
      }
    Each leg:
      {
        "departure_airport": {"id": "SGN", "name": "...", "time": "2026-06-20 08:40"},
        "arrival_airport":   {"id": "HAN", "name": "...", "time": "2026-06-20 10:50"},
        "duration": 130,
        "airline": "Bamboo Airways",
        "flight_number": "QH 208",
        "airplane": "Airbus A321",
        "travel_class": "Economy",
        "legroom": "29 in",
        "extensions": [...],
        "often_delayed_by_over_30_min": true  (optional)
      }
    """
    legs = flight.get("flights", [])
    first_leg = legs[0] if legs else {}
    last_leg  = legs[-1] if legs else {}

    # Airlines & flight numbers
    airlines = []
    flight_numbers = []
    often_delayed = False
    airplanes = []

    for leg in legs:
        airline = leg.get("airline", "")
        if airline and airline not in airlines:
            airlines.append(airline)
        fn = leg.get("flight_number", "")
        if fn:
            flight_numbers.append(fn)
        if leg.get("often_delayed_by_over_30_min"):
            often_delayed = True
        ap = leg.get("airplane", "")
        if ap and ap not in airplanes:
            airplanes.append(ap)

    # Stops & transit airports
    stops = max(len(legs) - 1, 0)
    stop_airports = [
        leg["arrival_airport"]["id"]
        for leg in legs[:-1]
        if leg.get("arrival_airport", {}).get("id")
    ] if stops > 0 else []

    # Origin / Destination / Times
    origin      = first_leg.get("departure_airport", {}).get("id", "")
    destination = last_leg.get("arrival_airport", {}).get("id", "")
    departure   = first_leg.get("departure_airport", {}).get("time", "")
    arrival     = last_leg.get("arrival_airport", {}).get("time", "")

    # Price & currency (currency comes from search params, default USD)
    price_total = float(flight.get("price", 0) or 0)

    # Duration in minutes
    duration_minutes = int(flight.get("total_duration", 0) or 0)

    # Cabin class (from first leg)
    cabin_raw = first_leg.get("travel_class", "Economy")
    cabin_class = cabin_raw.upper().replace(" ", "_")

    # Carbon
    carbon = flight.get("carbon_emissions", {})
    carbon_g = int(carbon.get("this_flight", 0) or 0)

    # Legroom (from first leg)
    legroom = first_leg.get("legroom", None)

    # Booking token
    booking_token = flight.get("departure_token", None)

    # Unique ID
    fn_str = "_".join(flight_numbers) if flight_numbers else "unknown"
    dep_str = departure.replace(" ", "T").replace(":", "") if departure else "0000"
    uid = f"apify_{fn_str}_{dep_str}"

    return {
        "id": uid,
        "source": "apify_google",
        "is_best": is_best,
        "airlines": airlines,
        "flight_numbers": flight_numbers,
        "origin": origin,
        "destination": destination,
        "departure": departure,
        "arrival": arrival,
        "duration_minutes": duration_minutes,
        "stops": stops,
        "stop_airports": stop_airports,
        "cabin_class": cabin_class,
        "price_total": price_total,
        "price_currency": "USD",
        "price_breakdown": {"base": price_total, "taxes": 0, "fees": 0},
        "segments": legs,
        "booking_token": booking_token,
        "booking_url": None,
        "airplane": ", ".join(airplanes) if airplanes else None,
        "legroom": legroom,
        "often_delayed": often_delayed,
        "carbon_g": carbon_g,
        "raw": flight,
    }


def deduplicate_flights(flights):
    """Keep lowest-price flight when flight_numbers + departure match."""
    seen = {}
    for f in flights:
        key = (tuple(f["flight_numbers"]), f["departure"])
        if key not in seen or f["price_total"] < seen[key]["price_total"]:
            seen[key] = f
    return list(seen.values())


def sort_by_price(flights):
    return sorted(flights, key=lambda f: f["price_total"])


def calculate_savings(baseline_price, alternative_price):
    savings = baseline_price - alternative_price
    pct = (savings / baseline_price * 100) if baseline_price > 0 else 0
    return {
        "amount": round(savings, 2),
        "percentage": round(pct, 1),
        "baseline": round(baseline_price, 2),
        "alternative": round(alternative_price, 2),
    }


def format_duration(minutes):
    if not minutes or minutes <= 0:
        return "N/A"
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m}m" if m else f"{h}h"


def format_results_table(flights, top_n=None, currency="USD"):
    """Format as markdown table."""
    if top_n:
        flights = flights[:top_n]
    lines = [
        "| # | ★ | Airlines | Flight | Route | Departure | Arrival | Duration | Stops | Price |",
        "|---|---|----------|--------|-------|-----------|---------|----------|-------|-------|",
    ]
    for i, f in enumerate(flights, 1):
        best  = "⭐" if f.get("is_best") else ""
        delay = " ⚠️" if f.get("often_delayed") else ""
        airline = ", ".join(f["airlines"])
        fn     = ", ".join(f["flight_numbers"])
        route  = f"{f['origin']} → {f['destination']}"
        dur    = format_duration(f["duration_minutes"])
        price  = f"${f['price_total']:,.0f}"
        stops  = str(f["stops"]) + (" ✈" if f["stops"] == 0 else "")
        lines.append(
            f"| {i} | {best} | {airline} | {fn}{delay} | {route} | "
            f"{f['departure']} | {f['arrival']} | {dur} | {stops} | {price} |"
        )
    return "\n".join(lines)


def to_frontend_card(flight):
    """Convert normalized flight to frontend-optimized dict (no raw data)."""
    return {
        "id": flight["id"],
        "is_best": flight.get("is_best", False),
        "airlines": flight["airlines"],
        "flight_numbers": flight["flight_numbers"],
        "origin": flight["origin"],
        "destination": flight["destination"],
        "departure": flight["departure"],
        "arrival": flight["arrival"],
        "duration_minutes": flight["duration_minutes"],
        "stops": flight["stops"],
        "stop_airports": flight.get("stop_airports", []),
        "cabin_class": flight.get("cabin_class", "ECONOMY"),
        "price_total": flight["price_total"],
        "price_currency": flight.get("price_currency", "USD"),
        "airplane": flight.get("airplane"),
        "legroom": flight.get("legroom"),
        "often_delayed": flight.get("often_delayed", False),
        "carbon_g": flight.get("carbon_g", 0),
    }


def get_search_summary(apify_items):
    """Extract search metadata from the Apify response."""
    if not apify_items:
        return {}
    item = apify_items[0] if isinstance(apify_items, list) else apify_items
    return {
        "search_parameters": item.get("search_parameters", {}),
        "search_metadata": item.get("search_metadata", {}),
        "search_timestamp": item.get("search_timestamp", ""),
    }
