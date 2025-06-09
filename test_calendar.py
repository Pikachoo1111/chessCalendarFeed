#!/usr/bin/env python3
"""
Unit tests for Chess Tournament Calendar Generator
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from generate_calendar import ChessCalendarGenerator

class TestChessCalendarGenerator:
    """Test suite for ChessCalendarGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ChessCalendarGenerator()
        
    def test_init(self):
        """Test initialization of ChessCalendarGenerator."""
        assert self.generator.source_url == "https://www.austinchesstournaments.com/events/"
        assert self.generator.llm_api_url == "https://ai.hackclub.com/chat/completions"
        assert self.generator.output_file == "calendar.ics"
    
    @patch('generate_calendar.requests.get')
    def test_scrape_events_success(self, mock_get):
        """Test successful event scraping."""
        # Mock HTML response
        mock_html = """
        <html>
            <body>
                <div class="event-card">
                    <h3>Austin Chess Championship</h3>
                    <p>Date: 2024-02-15</p>
                    <p>Location: Austin Chess Club</p>
                </div>
                <div class="event-card">
                    <h3>Spring Tournament</h3>
                    <p>Date: 2024-03-20</p>
                    <p>Location: Community Center</p>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.generator.scrape_events()
        
        assert "Austin Chess Championship" in result
        assert "Spring Tournament" in result
        assert "2024-02-15" in result
        assert "Austin Chess Club" in result
        mock_get.assert_called_once()
    
    @patch('generate_calendar.requests.get')
    def test_scrape_events_no_event_cards(self, mock_get):
        """Test scraping when no event cards are found."""
        mock_html = """
        <html>
            <body>
                <main>
                    <p>Upcoming tournaments will be posted here.</p>
                    <p>Check back soon for updates!</p>
                </main>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.generator.scrape_events()
        
        assert "Upcoming tournaments" in result
        assert "Check back soon" in result
    
    @patch('generate_calendar.requests.get')
    def test_scrape_events_request_failure(self, mock_get):
        """Test handling of request failures during scraping."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            self.generator.scrape_events()
    
    @patch('generate_calendar.requests.post')
    def test_call_llm_with_retry_success(self, mock_post):
        """Test successful LLM processing."""
        # Mock successful LLM response
        mock_events = [
            {
                "title": "Austin Chess Championship",
                "date": "2024-02-15",
                "time": "10:00",
                "location": "Austin Chess Club"
            },
            {
                "title": "Spring Tournament",
                "date": "2024-03-20",
                "time": "14:00",
                "location": "Community Center"
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(mock_events)
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        raw_text = "Some tournament text"
        result = self.generator.call_llm_with_retry(raw_text)
        
        assert len(result) == 2
        assert result[0]["title"] == "Austin Chess Championship"
        assert result[1]["date"] == "2024-03-20"
        mock_post.assert_called_once()
    
    @patch('generate_calendar.requests.post')
    def test_call_llm_with_retry_json_cleanup(self, mock_post):
        """Test LLM response cleanup (removing markdown code blocks)."""
        mock_events = [{"title": "Test Event", "date": "2024-01-01"}]
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": f"```json\n{json.dumps(mock_events)}\n```"
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.generator.call_llm_with_retry("test text")
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Event"
    
    @patch('generate_calendar.requests.post')
    def test_call_llm_with_retry_failure(self, mock_post):
        """Test LLM retry logic on failures."""
        # Mock response that raises KeyError (which is caught by the retry logic)
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "response"}  # Missing "choices" key
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError):
            self.generator.call_llm_with_retry("test text", max_retries=2)

        assert mock_post.call_count == 2
    
    def test_generate_ics_calendar(self):
        """Test ICS calendar generation."""
        events_data = [
            {
                "title": "Austin Chess Championship",
                "date": "2024-02-15",
                "time": "10:00",
                "location": "Austin Chess Club",
                "description": "Annual championship tournament"
            },
            {
                "title": "Spring Tournament",
                "date": "2024-03-20",
                "time": "14:00",
                "location": "Community Center"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change output file to temp directory
            original_output = self.generator.output_file
            self.generator.output_file = os.path.join(temp_dir, "test_calendar.ics")
            
            try:
                result = self.generator.generate_ics_calendar(events_data)
                
                assert os.path.exists(result)
                
                # Read and verify calendar content
                with open(result, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                assert "BEGIN:VCALENDAR" in content
                assert "END:VCALENDAR" in content
                assert "Austin Chess Championship" in content
                assert "Spring Tournament" in content
                assert "Austin Chess Club" in content
                
                # Count events
                event_count = content.count("BEGIN:VEVENT")
                assert event_count == 2
                
            finally:
                self.generator.output_file = original_output
    
    def test_generate_ics_calendar_invalid_event(self):
        """Test ICS generation with invalid event data."""
        events_data = [
            {
                "title": "Valid Event",
                "date": "2024-02-15",
                "time": "10:00"
            },
            {
                "title": "Invalid Event",
                "date": "invalid-date",  # Invalid date format
                "time": "25:00"  # Invalid time
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            original_output = self.generator.output_file
            self.generator.output_file = os.path.join(temp_dir, "test_calendar.ics")
            
            try:
                result = self.generator.generate_ics_calendar(events_data)
                
                # Should still create calendar with valid events
                assert os.path.exists(result)
                
                with open(result, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Should contain the valid event
                assert "Valid Event" in content
                # Should have only 1 event (invalid one skipped)
                event_count = content.count("BEGIN:VEVENT")
                assert event_count == 1
                
            finally:
                self.generator.output_file = original_output
    
    @patch.object(ChessCalendarGenerator, 'scrape_events')
    @patch.object(ChessCalendarGenerator, 'call_llm_with_retry')
    @patch.object(ChessCalendarGenerator, 'generate_ics_calendar')
    def test_run_success(self, mock_generate, mock_llm, mock_scrape):
        """Test successful end-to-end execution."""
        # Mock the pipeline
        mock_scrape.return_value = "Raw event text"
        mock_llm.return_value = [{"title": "Test Event", "date": "2024-01-01"}]
        mock_generate.return_value = "calendar.ics"
        
        result = self.generator.run()
        
        assert result == "calendar.ics"
        mock_scrape.assert_called_once()
        mock_llm.assert_called_once_with("Raw event text")
        mock_generate.assert_called_once()
    
    @patch.object(ChessCalendarGenerator, 'scrape_events')
    def test_run_no_data_scraped(self, mock_scrape):
        """Test handling when no data is scraped."""
        mock_scrape.return_value = ""
        
        with pytest.raises(ValueError, match="No event data scraped"):
            self.generator.run()

def test_main_function():
    """Test the main function."""
    with patch.object(ChessCalendarGenerator, 'run') as mock_run:
        mock_run.return_value = "calendar.ics"
        
        # Import and test main function
        from generate_calendar import main
        
        # Should not raise exception
        main()
        mock_run.assert_called_once()

def test_main_function_with_error():
    """Test main function error handling."""
    with patch.object(ChessCalendarGenerator, 'run') as mock_run:
        mock_run.side_effect = Exception("Test error")
        
        from generate_calendar import main
        
        with pytest.raises(SystemExit):
            main()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
