"""Unit tests for scoring module."""

import pytest
from llm_seo.scoring import calculate_scores


class TestCalculateScores:
    
    def test_empty_pages(self):
        result = calculate_scores([])
        assert result['pages'] == []
        assert result['site_score'] == 0
    
    def test_single_page(self):
        pages_data = [
            {
                'url': 'https://example.com',
                'score': 80,
                'checks': {}
            }
        ]
        
        result = calculate_scores(pages_data)
        assert result['site_score'] == 80
        assert len(result['pages']) == 1
    
    def test_multiple_pages(self):
        pages_data = [
            {'url': 'https://example.com/page1', 'score': 80, 'checks': {}},
            {'url': 'https://example.com/page2', 'score': 60, 'checks': {}},
            {'url': 'https://example.com/page3', 'score': 100, 'checks': {}}
        ]
        
        result = calculate_scores(pages_data)
        assert result['site_score'] == 80  # (80 + 60 + 100) / 3
        assert len(result['pages']) == 3
