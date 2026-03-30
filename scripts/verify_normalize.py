import sys, json
sys.path.append('scripts')
from normalize import extract_all_flights, sort_by_price, format_results_table, get_search_summary

with open('test_result.json', encoding='utf-8') as f:
    raw = json.load(f)

summary = get_search_summary(raw)
meta = summary.get('search_metadata', {})
print(f'Total flights found: {meta.get("total_flights_found")}')
print(f'Best: {meta.get("best_flights_count")}  Other: {meta.get("other_flights_count")}')
print()

flights = sort_by_price(extract_all_flights(raw))
print(format_results_table(flights, top_n=10))
print()
prices = [f["price_total"] for f in flights]
print(f'Price range: ${min(prices):,.0f} - ${max(prices):,.0f} USD')
print(f'Total normalized: {len(flights)} flights')
print(f'Airlines: {", ".join(sorted(set(a for f in flights for a in f["airlines"])))}')
