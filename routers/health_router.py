#!/usr/bin/env python3
"""Health check router."""

from fastapi import APIRouter
from scripts.config import APIFY_TOKEN, LLM_API_KEY

router = APIRouter()


@router.get("/health")
async def health_check():
    """Server status and API key validation."""
    return {
        "status": "ok",
        "service": "Travel Optimization Engine",
        "version": "1.0.0",
        "apis": {
            "apify": "configured" if APIFY_TOKEN else "missing",
            "llm": "configured" if LLM_API_KEY else "missing",
        },
    }
