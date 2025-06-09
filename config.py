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
- start_date (required): Start date in YYYY-MM-DD format
- end_date (optional): End date in YYYY-MM-DD format (only if event spans multiple days)
- time (optional): Start time in HH:MM format (24-hour) for single-day events
- location (optional): Venue or address
- description (optional): Additional details

For multi-day events (like camps, tournaments spanning several days):
- Include both start_date and end_date
- Do not include time (these will be all-day events)

For single-day events:
- Only include start_date
- Optionally include time

Only return valid JSON, no other text:

{text}
"""

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
