#!/usr/bin/env python3
"""
Bridge between AI tool calls and existing flight search scripts.
Wraps scripts/ functions as callable tools for the AI orchestrator.
"""

import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from apify_flight import search_flights
from normalize import (
    extract_all_flights,
    sort_by_price,
    format_results_table,
    to_frontend_card,
    calculate_savings,
    get_search_summary,
)


def tool_search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = None,
    adults: int = 1,
    children: int = 0,
    currency: str = "USD",
    max_stops: int = None,
) -> dict:
    """
    Execute flight search and return normalized results.
    Called by AI orchestrator when it decides to search flights.

    Returns dict with:
        - flights: list of frontend-ready flight cards
        - summary: search metadata
        - table: markdown table of results
    """
    try:
        raw_results = search_flights(
            departure_id=origin.upper(),
            arrival_id=destination.upper(),
            outbound_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            currency=currency,
            max_stops=max_stops,
        )

        if not raw_results:
            return {
                "status": "no_results",
                "flights": [],
                "message": f"No flights found for {origin} → {destination} on {departure_date}",
            }

        # Normalize and sort
        flights = sort_by_price(extract_all_flights(raw_results))
        summary = get_search_summary(raw_results)
        cards = [to_frontend_card(f) for f in flights]
        table = format_results_table(flights, top_n=10)

        # Savings vs most expensive
        if len(flights) >= 2:
            prices = [f["price_total"] for f in flights]
            savings_info = calculate_savings(max(prices), min(prices))
        else:
            savings_info = None

        return {
            "status": "ok",
            "total_results": len(flights),
            "flights": cards,
            "table": table,
            "summary": summary,
            "savings": savings_info,
            "price_range": {
                "min": min(f["price_total"] for f in flights),
                "max": max(f["price_total"] for f in flights),
                "currency": currency,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "flights": [],
            "message": f"Search failed: {str(e)}",
        }


def tool_get_date_matrix(origin: str, destination: str, departure_date: str, flex_days: int = 3) -> dict:
    """Mock matrix calculation for date optimization."""
    # In a real app this would query history or do multiple API calls
    return {
        "status": "ok",
        "origin": origin,
        "destination": destination,
        "matrix_data": "Generated price heatmap based on patterns",
        "best_depart": departure_date,
        "best_return": "N/A",
        "savings_estimate": "15-25%"
    }


def tool_analyze_fees(advertised_price: float, airline: str, carry_on: bool = True, checked_bags: int = 0) -> dict:
    """Calculate true total cost including typical hidden fees."""
    # Basic fee matrix mock for MVP
    fees = {
        "VietJet": {"carry_on": 0, "checked": 45, "seat": 12},
        "AirAsia": {"carry_on": 0, "checked": 50, "seat": 15},
        "VN Airlines": {"carry_on": 0, "checked": 0, "seat": 0},
        "Spirit": {"carry_on": 65, "checked": 60, "seat": 25}
    }
    
    airline_fee = fees.get(airline, {"carry_on": 0, "checked": 30, "seat": 10})
    
    total_fees = 0
    if carry_on and airline in ["Spirit"]:
        total_fees += airline_fee["carry_on"]
    total_fees += (checked_bags * airline_fee["checked"])
    total_fees += airline_fee["seat"] # Assume user wants to pick a seat
    
    return {
        "status": "ok",
        "airline": airline,
        "advertised_price": advertised_price,
        "total_fees": total_fees,
        "true_total": advertised_price + total_fees,
        "breakdown": {
            "carry_on_fee": airline_fee["carry_on"] if carry_on and airline in ["Spirit"] else 0,
            "checked_bag_fee": airline_fee["checked"] * checked_bags,
            "seat_selection_fee": airline_fee["seat"]
        }
    }


def tool_optimize_route(origin: str, destination: str, baseline_price: float, baseline_duration: float) -> dict:
    """Analyze alternative routes through strategic hubs."""
    # Mock hub logic
    saving_usd = baseline_price * 0.25
    extra_time = 3.5
    savings_per_hour = saving_usd / extra_time if extra_time > 0 else 0
    
    rating = "⭐⭐⭐" if savings_per_hour > 100 else ("⭐⭐" if savings_per_hour > 50 else "⭐")

    return {
        "status": "ok",
        "baseline_price": baseline_price,
        "baseline_duration": baseline_duration,
        "alternative": {
            "hub": "ICN" if origin == "HAN" else "TPE",
            "price": baseline_price - saving_usd,
            "duration": baseline_duration + extra_time,
            "savings_usd": saving_usd,
            "extra_time_hrs": extra_time,
            "savings_per_hour": savings_per_hour,
            "rating": rating
        }
    }


def tool_find_deals(route: str, airline: str = "Tất cả") -> dict:
    """Fetch potential deals, coupons, and discounts."""
    return {
        "status": "ok",
        "route": route,
        "deals": [
            {"name": "VietJet 0 VND Flash Sale", "confidence": "HIGH", "savings": "70-90% base fare"},
            {"name": "Techcombank Visa Discount", "confidence": "MEDIUM", "savings": "5% cashback"},
            {"name": "RetailMeNot Coupon", "confidence": "LOW", "savings": "$10 off"}
        ]
    }


def tool_calculate_flexibility_risk(saver_price: float, flex_price: float, schedule_certainty: int) -> dict:
    """Calculate break-even for flexible tickets."""
    premium = flex_price - saver_price
    loss_if_cancel = saver_price # Assuming full loss for saver
    
    if loss_if_cancel == 0:
        break_even = 0
    else:
        break_even = (premium / loss_if_cancel) * 100

    implied_change_prob = 100 - schedule_certainty
    recommendation = "BUY FLEX TICKET" if implied_change_prob > break_even else "BUY SAVER TICKET"

    return {
        "status": "ok",
        "saver_price": saver_price,
        "flex_price": flex_price,
        "premium": premium,
        "schedule_certainty": schedule_certainty,
        "break_even_probability_percent": round(break_even, 1),
        "user_change_prob_percent": implied_change_prob,
        "recommendation": recommendation
    }


def tool_negotiation_email(company_name: str, volume: int, routes: str) -> dict:
    """Generate a corporate negotiation email draft."""
    draft = f"Subject: {company_name} - {volume} Annual Business Flights - Partnership Discussion\n\nDear Corporate Sales Team,\n\nI am representing {company_name}. We have an annual volume of {volume} flights, primarily on {routes}. We are looking to consolidate our travel spend and seeking a 10-15% improvement on published fares..."
    
    return {
        "status": "ok",
        "email_draft": draft,
        "tips": "Send to Corporate Sales manager on a Tuesday morning. Don't reveal max budget."
    }


def tool_hidden_city_analysis(origin: str, destination: str, target_hidden_city: str) -> dict:
    """Analyze risk vs reward for hidden city ticketing."""
    return {
        "status": "ok",
        "warning": "Hidden city violates airline carriage contract.",
        "route_checked": f"{origin} -> {destination} -> {target_hidden_city}",
        "risks": [
            "Frequent flyer account suspension",
            "Checked bags will go to final destination",
            "Return leg canceled if missing first leg",
            "Fare difference retroactively charged"
        ]
    }


# Map tool name → function for the orchestrator
TOOL_REGISTRY = {
    "search_flights": tool_search_flights,
    "get_date_matrix": tool_get_date_matrix,
    "analyze_fees": tool_analyze_fees,
    "optimize_route": tool_optimize_route,
    "find_deals": tool_find_deals,
    "calculate_flexibility_risk": tool_calculate_flexibility_risk,
    "negotiation_email": tool_negotiation_email,
    "hidden_city_analysis": tool_hidden_city_analysis,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool by name with given arguments."""
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    func = TOOL_REGISTRY[tool_name]
    try:
        return func(**arguments)
    except TypeError as e:
        return {"status": "error", "message": f"Invalid arguments for {tool_name}: {e}"}
