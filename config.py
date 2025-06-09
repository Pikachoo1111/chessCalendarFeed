#!/usr/bin/env python3
"""
Configuration file for Chess Tournament Calendar Feed
"""

import os

# Source website configuration
SOURCE_URL = os.getenv("CHESS_CALENDAR_URL", "https://www.austinchesstournaments.com/events/")

# LLM API configuration
LLM_API_URL = "https://ai.hackclub.com/chat/completions"
LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2

# Calendar configuration
OUTPUT_FILE = os.getenv("CHESS_CALENDAR_OUTPUT", "calendar.ics")
CALENDAR_CREATOR = "Chess Tournament Calendar Feed"
DEFAULT_EVENT_DURATION_HOURS = 3

# Scraping configuration
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Event selectors (tried in order)
EVENT_SELECTORS = [
    '.event-card',
    '.event',
    '.tournament',
    '[class*="event"]',
    '[class*="tournament"]'
]

# LLM prompt template
LLM_PROMPT_TEMPLATE = """
Please convert the following chess tournament events text into a JSON array. 
Each event should have these fields:
- title (required): The tournament name
- date (required): Date in YYYY-MM-DD format
- time (optional): Time in HH:MM format (24-hour)
- location (optional): Venue or address
- description (optional): Additional details

Only return valid JSON, no other text:

{text}
"""

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
