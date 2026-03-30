#!/usr/bin/env python3
"""Direct flight search router — bypasses AI, calls Apify directly."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()


class SearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3, description="Origin IATA code")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination IATA code")
    departure_date: str = Field(..., description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(None, description="Return date YYYY-MM-DD")
    adults: int = Field(1, ge=1, le=9)
    children: int = Field(0, ge=0, le=9)
    infants: int = Field(0, ge=0, le=4)
    currency: str = Field("USD")
    max_stops: Optional[int] = Field(None, ge=0, le=3)
    max_price: Optional[float] = Field(None, gt=0)


class SearchResponse(BaseModel):
    status: str
    total_results: int
    flights: list
    search_metadata: dict


@router.post("/search", response_model=SearchResponse)
async def search_flights_endpoint(req: SearchRequest):
    """Search flights directly via Apify Google Flights."""
    try:
        from scripts.apify_flight import search_flights
        from scripts.normalize import extract_all_flights, sort_by_price, to_frontend_card

        raw_results = search_flights(
            departure_id=req.origin.upper(),
            arrival_id=req.destination.upper(),
            outbound_date=req.departure_date,
            return_date=req.return_date,
            adults=req.adults,
            children=req.children,
            infants=req.infants,
            currency=req.currency,
            max_stops=req.max_stops,
            max_price=req.max_price,
        )

        if not raw_results:
            return SearchResponse(
                status="no_results",
                total_results=0,
                flights=[],
                search_metadata={"query": req.model_dump()},
            )

        flights = sort_by_price(extract_all_flights(raw_results))
        cards = [to_frontend_card(f) for f in flights]

        return SearchResponse(
            status="ok",
            total_results=len(cards),
            flights=cards,
            search_metadata={
                "query": req.model_dump(),
                "source": "apify_google_flights",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")
