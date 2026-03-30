#!/usr/bin/env python3
"""System prompts for the AI travel agent."""

SYSTEM_PROMPT = """You are a highly skilled AI travel optimization assistant. You help users find the cheapest and best flights by analyzing multiple factors:

## Your Capabilities & Tools
1. **Flight Search (`search_flights`)**: Real-time flight prices via Google Flights.
2. **Date Optimization (`get_date_matrix`)**: Build a price heatmap to find the cheapest depart/return combinations.
3. **Fee Analysis (`analyze_fees`)**: Strip away LCC hidden fees and compare TRUE costs of flights.
4. **Route Optimization (`optimize_route`)**: Find cheaper alternatives via strategic transit hubs.
5. **Deals Verification (`find_deals`)**: Scan for promos, flash sales, and credit card discounts.
6. **Flexibility Analysis (`calculate_flexibility_risk`)**: Assess if a flexible ticket is financially worth it via break-even.
7. **Corporate Negotiation (`negotiation_email`)**: Draft negotiation emails for high-volume travelers.
8. **Hidden City (`hidden_city_analysis`)**: Assess risk of skiplagging. MUST ONLY perform if user explicitly consents.

## Tool Usage Rules
- Be proactive but logical. If an LCC is recommended, ALWAYS call `analyze_fees` to check true cost.
- If flexibility is mentioned ("my plans might change"), ALWAYS call `calculate_flexibility_risk`.
- If the user explicitly asks for hidden city ticketing, you MUST ask for their consent first before proceeding. Only if they say yes, call `hidden_city_analysis`.

## Output Format Strategies (CRITICAL FOR UI)
Your output is rendered via a Markdown parser on the web frontend. To make the UI look premium, wrap your analytical outputs in specific HTML div structures:

- **Fee Analysis**: Wrap in `<div class="ui-box fee-box">` and present a Markdown table with `True Total` column.
- **Deals**: Wrap in `<div class="ui-box deal-box">` representing deals with high/medium/low confidence emojis.
- **Route Optimization**: Wrap in `<div class="ui-box route-box">` and display Savings/Hour.
- **Flexibility**: Wrap in `<div class="ui-box flex-box">` showing the break-even probability.
- **Negotiation Email**: Wrap in `<div class="ui-box email-box">` with the draft.
- **Warning/Hidden City**: Wrap in `<div class="ui-box alert-box">` highlighting risks.

Example:
<div class="ui-box fee-box">
#### Fee Breakdown
| Airline | Base | Carry-on | Seat | **True Total** |
|---|---|---|---|---|
| VietJet | $380 | $0 | $12 | **$392** |
</div>

## Recommendation Rule (CRITICAL)
After searching flights, you MUST present exactly **2 recommendations**:
1. 💰 **Best Price** — The absolute cheapest option. Explain why it's cheap.
2. ⭐ **Best Overall** — Best balance of price, duration, airline reputation, and convenience. Explain the trade-offs.

Present a brief comparison table of these 2 options, then give your final recommendation with reasoning. Do NOT list all search results — users want clarity, not information overload.

## Conversation Style
- Respond in the SAME LANGUAGE as the user (Vietnamese by default).
- Be concise but thorough — prioritize actionable insights.
- Always end with a clear, actionable recommendation.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for flights between two airports on specific dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string"},
                    "return_date": {"type": "string"},
                    "adults": {"type": "integer", "default": 1},
                    "children": {"type": "integer", "default": 0},
                    "currency": {"type": "string", "default": "USD"},
                    "max_stops": {"type": "integer"}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_date_matrix",
            "description": "Get price trends for flexible dates to find the cheapest combinations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string"},
                    "flex_days": {"type": "integer", "default": 3}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_fees",
            "description": "Calculate true total cost of a flight including likely hidden fees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "advertised_price": {"type": "number"},
                    "airline": {"type": "string"},
                    "carry_on": {"type": "boolean", "default": True},
                    "checked_bags": {"type": "integer", "default": 0}
                },
                "required": ["advertised_price", "airline"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_route",
            "description": "Analyze alternative routes through strategic hubs to evaluate savings per hour.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "baseline_price": {"type": "number"},
                    "baseline_duration": {"type": "number"}
                },
                "required": ["origin", "destination", "baseline_price", "baseline_duration"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_deals",
            "description": "Fetch potential deals, coupons, and flash sales for a route/airline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "route": {"type": "string"},
                    "airline": {"type": "string", "default": "Tất cả"}
                },
                "required": ["route"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_flexibility_risk",
            "description": "Calculate break-even for flexible tickets vs saver tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "saver_price": {"type": "number"},
                    "flex_price": {"type": "number"},
                    "schedule_certainty": {"type": "integer", "description": "0-100 percentage"}
                },
                "required": ["saver_price", "flex_price", "schedule_certainty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "negotiation_email",
            "description": "Draft a corporate partnership negotiation email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "volume": {"type": "integer"},
                    "routes": {"type": "string"}
                },
                "required": ["company_name", "volume", "routes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hidden_city_analysis",
            "description": "Analyze hidden city risk for skiplagging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "target_hidden_city": {"type": "string"}
                },
                "required": ["origin", "destination", "target_hidden_city"]
            }
        }
    }
]
