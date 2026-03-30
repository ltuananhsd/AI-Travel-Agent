#!/usr/bin/env python3
"""Fee comparison router — compares true costs of multiple flights."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


class FlightEntry(BaseModel):
    airline: str = Field(..., description="Airline name")
    price: float = Field(..., gt=0, description="Advertised price")
    carry_on: bool = Field(True, description="Needs carry-on bag")
    checked_bags: int = Field(0, ge=0, le=5, description="Number of checked bags")


class CompareRequest(BaseModel):
    flights: List[FlightEntry] = Field(..., min_length=2, max_length=5)


class FeeBreakdown(BaseModel):
    airline: str
    advertised_price: float
    carry_on_fee: float
    checked_bag_fee: float
    seat_fee: float
    total_fees: float
    true_total: float


class CompareResponse(BaseModel):
    status: str
    results: List[FeeBreakdown]
    cheapest_advertised: str
    cheapest_true: str
    biggest_hidden_cost: str


@router.post("/compare-fees", response_model=CompareResponse)
async def compare_fees_endpoint(req: CompareRequest):
    """Compare true costs of multiple flights side by side."""
    try:
        from engine.tool_functions import tool_analyze_fees

        results = []
        for flight in req.flights:
            analysis = tool_analyze_fees(
                advertised_price=flight.price,
                airline=flight.airline,
                carry_on=flight.carry_on,
                checked_bags=flight.checked_bags,
            )

            results.append(FeeBreakdown(
                airline=flight.airline,
                advertised_price=flight.price,
                carry_on_fee=analysis["breakdown"]["carry_on_fee"],
                checked_bag_fee=analysis["breakdown"]["checked_bag_fee"],
                seat_fee=analysis["breakdown"]["seat_selection_fee"],
                total_fees=analysis["total_fees"],
                true_total=analysis["true_total"],
            ))

        # Sort by true total
        results.sort(key=lambda r: r.true_total)

        # Find insights
        cheapest_adv = min(req.flights, key=lambda f: f.price)
        cheapest_true = results[0]
        biggest_hidden = max(results, key=lambda r: r.total_fees)

        return CompareResponse(
            status="ok",
            results=results,
            cheapest_advertised=cheapest_adv.airline,
            cheapest_true=cheapest_true.airline,
            biggest_hidden_cost=f"{biggest_hidden.airline} (+${biggest_hidden.total_fees:.0f} phí ẩn)",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fee comparison failed: {str(e)}")
