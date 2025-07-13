"""Unit tests for crawler module."""

import pytest
from unittest.mock import Mock, patch
from llm_seo.crawler import get_internal_links, fetch_page, RateLimiter


class TestGetInternalLinks:
    
    def test_extract_internal_links(self):
        html = '''<html><body>
            <a href="/page1">Internal 1</a>
            <a href="/page2">Internal 2</a>
            <a href="https://external.com/page">External</a>
            <a href="mailto:test@example.com">Email</a>
        </body></html>'''
        
        links = get_internal_links(html, "https://example.com")
        
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://external.com/page" not in links
        assert len([l for l in links if "example.com" in l]) == 2
    
    def test_no_links(self):
        html = "<html><body><p>No links here</p></body></html>"
        links = get_internal_links(html, "https://example.com")
        assert links == []


class TestFetchPage:
    
    @patch('llm_seo.crawler.requests.get')
    def test_successful_fetch(self, mock_get):
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        rate_limiter = RateLimiter(delay=0)  # No delay for tests
        result = fetch_page("https://example.com", rate_limiter)
        
        assert result['url'] == "https://example.com"
        assert result['html'] == "<html><body>Test</body></html>"
        assert result['status_code'] == 200
        assert result['error'] is None
    
    @patch('llm_seo.crawler.requests.get')
    def test_fetch_error(self, mock_get):
        mock_get.side_effect = Exception("Connection error")
        
        rate_limiter = RateLimiter(delay=0)
        result = fetch_page("https://example.com", rate_limiter)
        
        assert result['url'] == "https://example.com"
        assert result['html'] is None
        assert result['error'] == "Connection error"


class TestRateLimiter:
    
    def test_rate_limiter_delay(self):
        import time
        
        rate_limiter = RateLimiter(delay=0.1)
        
        start_time = time.time()
        rate_limiter.wait()
        rate_limiter.wait()
        end_time = time.time()
        
        # Should have waited at least 0.1 seconds between calls
        assert end_time - start_time >= 0.1
