---
name: flight-search
description: Search for real-time flights using Google Flights data via Apify. Use when user asks to find flights, search tickets, check availability or prices for specific routes and dates. Triggers on keywords: tìm vé, search flights, find flights, book flight, flight from, fly from, check flights, cheap flights, vé máy bay, giá vé. Requires departure_id, arrival_id, outbound_date. Returns best + other flights with price, duration, stops, airline.
---

# Flight Search — Apify Google Flights

Real-time Google Flights data via `scripts/apify_flight.py`.

## Quick usage

```python
import sys; sys.path.append("scripts")
from apify_flight import search_flights
from normalize import extract_all_flights, format_results_table, sort_by_price

raw = search_flights(
    departure_id="SGN",
    arrival_id="HAN",
    outbound_date="2026-06-20",
    return_date="2026-06-25",   # omit for one-way
    adults=1,
    currency="USD",
)

flights = sort_by_price(extract_all_flights(raw))
print(format_results_table(flights, top_n=10))
```

## Input Parameters

| Param | Required | Example | Notes |
|-------|----------|---------|-------|
| `departure_id` | ✅ | `"SGN"` | IATA code |
| `arrival_id` | ✅ | `"HAN"` | IATA code |
| `outbound_date` | ✅ | `"2026-06-20"` | YYYY-MM-DD |
| `return_date` | ❌ | `"2026-06-25"` | Omit = one-way |
| `adults` | ❌ | `1` | Default: 1 |
| `children` | ❌ | `0` | Age 2-11 |
| `infants` | ❌ | `0` | Under 2 |
| `currency` | ❌ | `"USD"` | Default: USD |
| `max_stops` | ❌ | `0` | 0=direct only |
| `max_price` | ❌ | `300` | Price ceiling |
| `exclude_basic` | ❌ | `True` | Skip basic economy |
| `max_pages` | ❌ | `1` | More pages = more results, slower |

## Response Schema

Each normalized flight has:
```python
{
  "id": "apify_QH 208_2026-06-20T0840",
  "source": "apify_google",
  "is_best": True,             # Google's recommendation
  "airlines": ["Bamboo Airways"],
  "flight_numbers": ["QH 208"],
  "origin": "SGN",
  "destination": "HAN",
  "departure": "2026-06-20 08:40",
  "arrival": "2026-06-20 10:50",
  "duration_minutes": 130,
  "stops": 0,
  "stop_airports": [],
  "cabin_class": "ECONOMY",
  "price_total": 163.0,
  "price_currency": "USD",
  "airplane": "Airbus A321",
  "legroom": "29 in",
  "often_delayed": False,
  "carbon_g": 136000,
  "booking_token": "...",      # use for price verification
}
```

## Normalize Helpers

```python
from normalize import (
    extract_all_flights,    # [raw_items] → [flight_dicts]
    sort_by_price,          # sort ascending
    deduplicate_flights,    # remove duplicates
    format_results_table,   # → markdown table
    format_duration,        # 130 → "2h 10m"
    calculate_savings,      # (base, alt) → {amount, percentage}
    get_search_summary,     # search params + metadata
)
```

## Common Patterns

**Direct flights only:**
```python
raw = search_flights(..., max_stops=0)
```

**Best deals (sorted, deduped, top 5):**
```python
flights = sort_by_price(deduplicate_flights(extract_all_flights(raw)))[:5]
```

**Separate best vs other:**
```python
all_flights = extract_all_flights(raw)
best   = [f for f in all_flights if f["is_best"]]
others = [f for f in all_flights if not f["is_best"]]
```

## Notes
- Apify runs take **30–90 seconds** per search
- `best_flights` = Google's curated top picks (usually 3)
- `other_flights` = remaining results (up to ~60 per page)
- `departure_token` can be used with the Apify actor to get return flight options
