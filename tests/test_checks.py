"""Unit tests for check functions."""

import pytest
from unittest.mock import Mock, patch
from llm_seo.checks import (
    check_robots, check_meta_robots, check_h1, 
    check_alt_text, check_jsonld
)


class TestCheckRobots:
    
    @patch('llm_seo.checks.requests.get')
    def test_robots_allows_bots(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nAllow: /"
        mock_get.return_value = mock_response
        
        result = check_robots("https://example.com")
        assert result['passed'] is True
        assert "allows bot access" in result['message']
    
    @patch('llm_seo.checks.requests.get')
    def test_robots_blocks_bots(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /"
        mock_get.return_value = mock_response
        
        result = check_robots("https://example.com")
        assert result['passed'] is False
        assert "blocks bot access" in result['message']
    
    @patch('llm_seo.checks.requests.get')
    def test_robots_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = check_robots("https://example.com")
        assert result['passed'] is False
        assert "not found" in result['message']


class TestCheckMetaRobots:
    
    def test_no_meta_robots(self):
        html = "<html><head></head><body></body></html>"
        result = check_meta_robots(html)
        assert result['passed'] is True
        assert "No restrictive" in result['message']
    
    def test_meta_robots_noindex(self):
        html = '<html><head><meta name="robots" content="noindex"></head></html>'
        result = check_meta_robots(html)
        assert result['passed'] is False
        assert "restricts indexing" in result['message']
    
    def test_meta_robots_allows_indexing(self):
        html = '<html><head><meta name="robots" content="index,follow"></head></html>'
        result = check_meta_robots(html)
        assert result['passed'] is True
        assert "allows indexing" in result['message']


class TestCheckH1:
    
    def test_h1_present(self):
        html = "<html><body><h1>Main Title</h1></body></html>"
        result = check_h1(html)
        assert result['passed'] is True
        assert "Main Title" in result['message']
    
    def test_no_h1(self):
        html = "<html><body><h2>Subtitle</h2></body></html>"
        result = check_h1(html)
        assert result['passed'] is False
        assert "No H1 tags found" in result['message']
    
    def test_empty_h1(self):
        html = "<html><body><h1></h1></body></html>"
        result = check_h1(html)
        assert result['passed'] is False
        assert "empty" in result['message']


class TestCheckAltText:
    
    def test_no_images(self):
        html = "<html><body><p>No images here</p></body></html>"
        result = check_alt_text(html)
        assert result['passed'] is True
        assert "No images found" in result['message']
    
    def test_all_images_have_alt(self):
        html = '''<html><body>
            <img src="image1.jpg" alt="Description 1">
            <img src="image2.jpg" alt="Description 2">
        </body></html>'''
        result = check_alt_text(html)
        assert result['passed'] is True
        assert "All 2 images have alt text" in result['message']
    
    def test_missing_alt_text(self):
        html = '''<html><body>
            <img src="image1.jpg" alt="Description 1">
            <img src="image2.jpg">
        </body></html>'''
        result = check_alt_text(html)
        assert result['passed'] is False
        assert "missing alt text" in result['message']
    
    def test_empty_alt_text(self):
        html = '''<html><body>
            <img src="image1.jpg" alt="">
        </body></html>'''
        result = check_alt_text(html)
        assert result['passed'] is False
        assert "empty alt text" in result['message']


class TestCheckJsonLD:
    
    def test_no_jsonld(self):
        html = "<html><body><p>No structured data</p></body></html>"
        result = check_jsonld(html)
        assert result['passed'] is False
        assert "No JSON-LD" in result['message']
    
    def test_valid_jsonld(self):
        html = '''<html><head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Test Article"
            }
            </script>
        </head></html>'''
        result = check_jsonld(html)
        assert result['passed'] is True
        assert "Article" in result['message']
    
    def test_invalid_jsonld(self):
        html = '''<html><head>
            <script type="application/ld+json">
            { invalid json
            </script>
        </head></html>'''
        result = check_jsonld(html)
        assert result['passed'] is False
        assert "invalid or empty" in result['message']
