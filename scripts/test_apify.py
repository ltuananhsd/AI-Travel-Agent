#!/usr/bin/env python3
"""
Quick test script — Apify Google Flights Scraper
Run: python scripts/test_apify.py
"""

import sys
import json
from pathlib import Path

# Add scripts/ to path for config/normalize — apify_client is installed package
scripts_dir = str(Path(__file__).parent)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from apify_client import ApifyClient
from config import APIFY_TOKEN, APIFY_ACTOR_ID
from normalize import extract_all_flights, sort_by_price, format_results_table, format_duration, get_search_summary

# ── Test params ───────────────────────────────────────────────────────────────
TEST_INPUT = {
    "departure_id":  "SGN",
    "arrival_id":    "HAN",
    "outbound_date": "2026-06-20",
    "return_date":   "2026-06-25",
    "adults": 1,
    "currency": "USD",
    "hl": "en",
    "gl": "us",
    "exclude_basic": False,
    "max_pages": 1,
}
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 65)
    print("  ✈  Apify Google Flights — Test Script")
    print("=" * 65)
    print(f"  Route  : {TEST_INPUT['departure_id']} → {TEST_INPUT['arrival_id']}")
    print(f"  Depart : {TEST_INPUT['outbound_date']}")
    print(f"  Return : {TEST_INPUT.get('return_date', 'one-way')}")
    print(f"  Adults : {TEST_INPUT['adults']}")
    print(f"  Actor  : {APIFY_ACTOR_ID}")
    print("=" * 65)
    print("Connecting to Apify... (may take 30–90 seconds)\n")

    client = ApifyClient(APIFY_TOKEN)

    try:
        run = client.actor(APIFY_ACTOR_ID).call(run_input=TEST_INPUT)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

    raw_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    # Search metadata
    summary = get_search_summary(raw_items)
    meta = summary.get("search_metadata", {})
    print(f"✅ Apify run complete!")
    print(f"   Total flights found : {meta.get('total_flights_found', '?')}")
    print(f"   Best flights        : {meta.get('best_flights_count', '?')}")
    print(f"   Other flights       : {meta.get('other_flights_count', '?')}")
    print(f"   Pages processed     : {meta.get('pages_processed', '?')}\n")

    # Normalize all flights
    flights = sort_by_price(extract_all_flights(raw_items))

    if not flights:
        print("⚠️  No flights extracted. Check raw data in test_result.json")
        sys.exit(0)

    # Print table (top 15)
    print(format_results_table(flights, top_n=15))
    print()

    # Price range
    prices = [f["price_total"] for f in flights]
    print(f"💰 Price range : ${min(prices):,.0f} – ${max(prices):,.0f} USD")
    print(f"📊 Airlines    : {', '.join(sorted(set(a for f in flights for a in f['airlines'])))}")
    best_count = sum(1 for f in flights if f["is_best"])
    print(f"⭐ Best picks  : {best_count} flights marked as Google's best")

    # Save raw + normalized
    output_raw  = Path(__file__).parent.parent / "test_result.json"
    output_norm = Path(__file__).parent.parent / "test_result_normalized.json"

    with open(output_raw, "w", encoding="utf-8") as f:
        json.dump(raw_items, f, indent=2, ensure_ascii=False)
    with open(output_norm, "w", encoding="utf-8") as f:
        json.dump(flights, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Raw data saved    → test_result.json")
    print(f"📁 Normalized saved  → test_result_normalized.json")
    print("=" * 65)


if __name__ == "__main__":
    main()
