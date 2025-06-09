#!/usr/bin/env python3
"""
Chess Tournament Calendar Feed Generator

This script scrapes chess tournament data from AustinChessTournaments.com,
uses an LLM to structure the data, and generates an ICS calendar file.
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from ics import Calendar, Event
from dateutil.parser import parse as parse_date
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class ChessCalendarGenerator:
    """Main class for generating chess tournament calendar feeds."""
    
    def __init__(self):
        self.source_url = config.SOURCE_URL
        self.llm_api_url = config.LLM_API_URL
        self.output_file = config.OUTPUT_FILE
        
    def scrape_events(self) -> str:
        """Scrape event data from the chess tournaments website."""
        logger.info(f"Scraping events from {self.source_url}")
        
        try:
            headers = {
                'User-Agent': config.USER_AGENT
            }
            response = requests.get(self.source_url, headers=headers, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors to find event cards
            event_selectors = config.EVENT_SELECTORS
            
            event_cards = []
            for selector in event_selectors:
                event_cards = soup.select(selector)
                if event_cards:
                    logger.info(f"Found {len(event_cards)} events using selector: {selector}")
                    break
            
            if not event_cards:
                # Fallback: get all text content from main content areas
                logger.warning("No event cards found, using fallback text extraction")
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    return main_content.get_text(separator="\n", strip=True)
                return soup.get_text(separator="\n", strip=True)
            
            # Extract text from event cards
            text_blocks = []
            for card in event_cards:
                text = card.get_text(separator="\n", strip=True)
                if text:
                    text_blocks.append(text)
            
            raw_text = "\n\n".join(text_blocks)
            logger.info(f"Extracted {len(raw_text)} characters of event data")
            return raw_text
            
        except requests.RequestException as e:
            logger.error(f"Failed to scrape events: {e}")
            raise
    
    def call_llm_with_retry(self, raw_text: str, max_retries: int = 3, delay: int = 2) -> List[Dict]:
        """Convert raw text to structured JSON using LLM with retry logic."""
        logger.info("Converting raw text to structured JSON using LLM")
        
        prompt = f"""
Please convert the following chess tournament events text into a JSON array. 
Each event should have these fields:
- title (required): The tournament name
- date (required): Date in YYYY-MM-DD format
- time (optional): Time in HH:MM format (24-hour)
- location (optional): Venue or address
- description (optional): Additional details

Only return valid JSON, no other text:

{raw_text[:4000]}  # Limit text to avoid token limits
"""
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"LLM attempt {attempt}/{max_retries}")
                
                response = requests.post(
                    self.llm_api_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                content = response.json()["choices"][0]["message"]["content"]
                
                # Clean up the response (remove markdown code blocks if present)
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # Parse JSON
                structured_data = json.loads(content)
                
                # Validate structure
                if not isinstance(structured_data, list):
                    raise ValueError("Response is not a JSON array")
                
                valid_events = []
                for event in structured_data:
                    if isinstance(event, dict) and "title" in event and "date" in event:
                        valid_events.append(event)
                
                if not valid_events:
                    raise ValueError("No valid events found in JSON response")
                
                logger.info(f"Successfully parsed {len(valid_events)} events")
                return valid_events
                
            except (json.JSONDecodeError, KeyError, ValueError, requests.RequestException) as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to get valid JSON after {max_retries} attempts")
                    raise RuntimeError(f"LLM processing failed after {max_retries} attempts: {e}")
    
    def generate_ics_calendar(self, events_data: List[Dict]) -> str:
        """Generate ICS calendar file from structured event data."""
        logger.info(f"Generating ICS calendar with {len(events_data)} events")
        
        calendar = Calendar()
        calendar.creator = "Chess Tournament Calendar Feed"
        
        for event_data in events_data:
            try:
                event = Event()
                event.name = event_data["title"]
                
                # Parse date and time
                date_str = event_data["date"]
                time_str = event_data.get("time", "12:00")
                
                # Handle various date formats
                try:
                    event_date = parse_date(date_str)
                except:
                    # Fallback parsing
                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Combine date and time
                if ":" in time_str:
                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    event_datetime = event_date.replace(hour=hour, minute=minute)
                else:
                    event_datetime = event_date.replace(hour=12, minute=0)
                
                event.begin = event_datetime
                event.end = event_datetime + timedelta(hours=3)  # Default 3-hour duration
                
                if "location" in event_data:
                    event.location = event_data["location"]
                
                if "description" in event_data:
                    event.description = event_data["description"]
                
                calendar.events.add(event)
                logger.debug(f"Added event: {event.name} on {event.begin}")
                
            except Exception as e:
                logger.warning(f"Failed to process event {event_data.get('title', 'Unknown')}: {e}")
                continue
        
        # Write calendar to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(calendar.serialize_iter())
        
        logger.info(f"Calendar saved to {self.output_file}")
        return self.output_file
    
    def run(self) -> str:
        """Main execution method."""
        logger.info("Starting chess calendar generation")
        
        try:
            # Step 1: Scrape events
            raw_text = self.scrape_events()
            
            if not raw_text.strip():
                raise ValueError("No event data scraped from website")
            
            # Step 2: Structure data with LLM
            structured_events = self.call_llm_with_retry(raw_text)
            
            # Step 3: Generate ICS calendar
            output_file = self.generate_ics_calendar(structured_events)
            
            logger.info("Chess calendar generation completed successfully")
            return output_file
            
        except Exception as e:
            logger.error(f"Calendar generation failed: {e}")
            raise

def main():
    """Main entry point."""
    try:
        generator = ChessCalendarGenerator()
        output_file = generator.run()
        print(f"[SUCCESS] Calendar generated successfully: {output_file}")

    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)

if __name__ == "__main__":
    main()
