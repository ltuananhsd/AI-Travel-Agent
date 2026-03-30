#!/usr/bin/env python3
"""
Apify Google Flights Client
Replaces Kiwi Tequila + Amadeus as the sole flight data source.

Actor: johnvc~google-flights-data-scraper (ID: 1dYHRKkEBHBPd0JM7)
Docs:  https://apify.com/johnvc/google-flights-data-scraper-flight-and-price-search

Usage:
    from scripts.apify_client import search_flights
    results = search_flights("SGN", "HAN", "2026-06-20")

Environment:
    APIFY_TOKEN: Your Apify API token
"""

import sys
import json
import argparse
from pathlib import Path

try:
    from apify_client import ApifyClient
except ImportError:
    print("Error: 'apify-client' library required. Install with: pip install apify-client")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from config import APIFY_TOKEN, DEFAULTS

# Actor ID for johnvc~google-flights-data-scraper
ACTOR_ID = "1dYHRKkEBHBPd0JM7"


def _get_client():
    """Return authenticated ApifyClient."""
    if not APIFY_TOKEN:
        print("Error: APIFY_TOKEN environment variable not set.")
        print("Get your token at: https://console.apify.com/account/integrations")
        print("Then set: $env:APIFY_TOKEN='apify_api_...' (PowerShell)")
        sys.exit(1)
    return ApifyClient(APIFY_TOKEN)


def search_flights(
    departure_id,
    arrival_id,
    outbound_date,
    return_date=None,
    adults=None,
    children=0,
    infants=0,
    currency=None,
    max_stops=None,
    max_price=None,
    airlines=None,
    exclude_basic=False,
    max_pages=1,
    hl="en",
    gl="us",
):
    """
    Search flights via Apify Google Flights scraper.

    Args:
        departure_id:  Origin IATA code (e.g., "SGN")
        arrival_id:    Destination IATA code (e.g., "HAN")
        outbound_date: Departure date "YYYY-MM-DD"
        return_date:   Return date "YYYY-MM-DD" (None = one-way)
        adults:        Number of adult passengers
        children:      Number of children
        infants:       Number of infants
        currency:      Currency code (default: USD)
        max_stops:     Maximum number of stops (None = any)
        max_price:     Maximum price filter (None = no limit)
        airlines:      List of airline codes to filter (None = all)
        exclude_basic: Exclude basic economy fares
        max_pages:     Number of result pages to scrape
        hl:            Language code (en, vi, ...)
        gl:            Country code (us, vn, ...)

    Returns:
        List of normalized flight dicts (see normalize.py for schema)
    """
    client = _get_client()

    run_input = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "adults": adults or DEFAULTS["adults"],
        "children": children,
        "infants": infants,
        "currency": currency or DEFAULTS["currency"],
        "hl": hl,
        "gl": gl,
        "exclude_basic": exclude_basic,
        "max_pages": max_pages,
    }

    # Optional filters
    if return_date:
        run_input["return_date"] = return_date
    if max_stops is not None:
        run_input["max_stops"] = max_stops
    if max_price is not None:
        run_input["max_price"] = max_price
    if airlines:
        run_input["airlines"] = airlines

    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input)
        items = list(
            client.dataset(run["defaultDatasetId"]).iterate_items()
        )
        return items
    except Exception as e:
        print(f"Apify API Error: {e}")
        return []


def search_flights_normalized(
    departure_id,
    arrival_id,
    outbound_date,
    return_date=None,
    **kwargs,
):
    """
    Search flights and return normalized unified format.
    Convenience wrapper around search_flights() + normalize.
    """
    from normalize import extract_all_flights

    raw_results = search_flights(
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        return_date=return_date,
        **kwargs,
    )
    return extract_all_flights(raw_results)


def main():
    parser = argparse.ArgumentParser(
        description="Search flights via Apify Google Flights Scraper"
    )
    parser.add_argument("--from", dest="departure_id", required=True, help="Origin IATA (e.g., SGN)")
    parser.add_argument("--to", dest="arrival_id", required=True, help="Destination IATA (e.g., HAN)")
    parser.add_argument("--depart", required=True, help="Departure date YYYY-MM-DD")
    parser.add_argument("--return", dest="return_date", help="Return date YYYY-MM-DD (omit = one-way)")
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--children", type=int, default=0)
    parser.add_argument("--infants", type=int, default=0)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--max-stops", type=int, default=None)
    parser.add_argument("--max-price", type=float, default=None)
    parser.add_argument("--exclude-basic", action="store_true")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--raw", action="store_true", help="Print raw API response")
    parser.add_argument("--output", default=None, help="Save results to JSON file")

    args = parser.parse_args()

    print(f"Searching: {args.departure_id} → {args.arrival_id}")
    print(f"Date: {args.depart}" + (f" | Return: {args.return_date}" if args.return_date else " (one-way)"))
    print(f"Passengers: {args.adults}A {args.children}C {args.infants}I  |  Currency: {args.currency}")
    print("Fetching from Apify Google Flights...\n")

    if args.raw:
        results = search_flights(
            departure_id=args.departure_id,
            arrival_id=args.arrival_id,
            outbound_date=args.depart,
            return_date=args.return_date,
            adults=args.adults,
            children=args.children,
            infants=args.infants,
            currency=args.currency,
            max_stops=args.max_stops,
            max_price=args.max_price,
            exclude_basic=args.exclude_basic,
            max_pages=args.max_pages,
        )
    else:
        results = search_flights_normalized(
            departure_id=args.departure_id,
            arrival_id=args.arrival_id,
            outbound_date=args.depart,
            return_date=args.return_date,
            adults=args.adults,
            children=args.children,
            infants=args.infants,
            currency=args.currency,
            max_stops=args.max_stops,
            max_price=args.max_price,
            exclude_basic=args.exclude_basic,
            max_pages=args.max_pages,
        )

    print(f"Found {len(results)} options\n")

    if not args.raw:
        for i, opt in enumerate(results, 1):
            airlines = ", ".join(opt.get("airlines", []))
            price = f"${opt.get('price_total', 0):,.0f} {opt.get('price_currency', '')}"
            stops = opt.get("stops", "?")
            dur = opt.get("duration_minutes", 0)
            duration = f"{dur // 60}h {dur % 60}m" if dur else "N/A"
            dep = str(opt.get("departure", ""))[:16]
            print(f"#{i:2d}  {price:<14}  {dep}  {duration:<8}  {stops} stop(s)  [{airlines}]")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
