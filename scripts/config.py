#!/usr/bin/env python3
"""Shared configuration for Travel Optimization Engine — Apify + Custom LLM."""

import os
import sys
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# --- API Credentials ---
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")

# LLM API (OpenAI-compatible)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "ces-chatbot-gpt-5.4")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://9router.vuhai.io.vn/v1")

# --- Apify Actor ---
APIFY_ACTOR_ID = "1dYHRKkEBHBPd0JM7"  # johnvc~google-flights-data-scraper

# --- Default Search Parameters ---
DEFAULTS = {
    "adults": 1,
    "children": 0,
    "infants": 0,
    "currency": "USD",
    "max_stops": None,       # None = no limit
    "max_price": None,       # None = no limit
    "cabin_class": "ECONOMY",
    "max_results": 20,
    "request_timeout": 120,  # seconds (Apify runs can take longer)
    "max_retries": 3,
    "exclude_basic": False,
    "max_pages": 1,
    "hl": "en",
    "gl": "us",
}


def validate_keys():
    """Check that APIFY_TOKEN is set. Exit with message if missing."""
    if not APIFY_TOKEN:
        print("ERROR: Missing APIFY_TOKEN", file=sys.stderr)
        print("Set in .env file or environment: APIFY_TOKEN=apify_api_...", file=sys.stderr)
        print("Get token at: https://console.apify.com/account/integrations", file=sys.stderr)
        sys.exit(1)
