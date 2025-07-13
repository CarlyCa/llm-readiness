"""Unit tests for LLM analysis module."""

import pytest
from unittest.mock import Mock, patch
from llm_seo.llm_analysis import (
    check_structured_data_richness,
    check_content_readability,
    extract_llm_readable_content,
    detect_duplicate_content,
    generate_llm_recommendations
)


class TestStructuredDataRichness:
    
    def test_no_structured_data(self):
        html = "<html><body><p>No structured data</p></body></html>"
        result = check_structured_data_richness(html)
        assert result['passed'] is False
        assert result['data']['total_schemas'] == 0
    
    def test_llm_friendly_schemas(self):
        html = '''<html><head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "What is this?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "This is a test."
                        }
                    }
                ]
            }
            </script>
        </head></html>'''
        result = check_structured_data_richness(html)
        assert result['passed'] is True
        assert 'FAQPage' in result['data']['llm_friendly_types']
        assert result['data']['richness_score'] > 0
    
    def test_non_llm_friendly_schemas(self):
        html = '''<html><head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": "Example Site"
            }
            </script>
        </head></html>'''
        result = check_structured_data_richness(html)
        assert result['passed'] is False
        assert result['data']['total_schemas'] == 1
        assert len(result['data']['llm_friendly_types']) == 0


class TestContentReadability:
    
    def test_insufficient_content(self):
        html = "<html><body><p>Short</p></body></html>"
        result = check_content_readability(html)
        assert result['passed'] is False
        assert "Insufficient content" in result['message']
    
    def test_good_readability(self):
        html = '''<html><body>
            <p>This is a well-written article with clear sentences. The content is easy to read and understand. 
            It provides valuable information in a structured format. The sentences are not too long or complex.
            This makes it perfect for both human readers and AI systems to process effectively.</p>
        </body></html>'''
        result = check_content_readability(html)
        assert result['data']['word_count'] > 30
        assert result['data']['flesch_reading_ease'] > 0
        assert result['data']['readability_score'] >= 0
    
    def test_complex_content(self):
        html = '''<html><body>
            <p>The implementation of sophisticated algorithmic methodologies necessitates comprehensive 
            understanding of multifaceted computational paradigms, thereby requiring extensive analytical 
            capabilities and theoretical foundations in advanced mathematical constructs.</p>
        </body></html>'''
        result = check_content_readability(html)
        assert result['data']['flesch_reading_ease'] < 50  # Should be harder to read


class TestLLMContentAnalysis:
    
    def test_llm_friendly_content(self):
        html = '''<html><body>
            <h1>Main Title</h1>
            <h2>Subtitle</h2>
            <p>This is a paragraph with good content.</p>
            <ul><li>List item 1</li><li>List item 2</li></ul>
            <img src="test.jpg" alt="Test image">
        </body></html>'''
        result = extract_llm_readable_content(html, "https://example.com")
        assert result['data']['easily_readable']['headings'] == 2
        assert result['data']['easily_readable']['paragraphs'] == 1
        assert result['data']['easily_readable']['lists'] == 1
        assert result['data']['easily_readable']['alt_text_images'] == 1
    
    def test_challenging_content(self):
        html = '''<html><body>
            <table><tr><td>Data</td></tr></table>
            <form><input type="text"></form>
            <img src="test.jpg">
        </body></html>'''
        result = extract_llm_readable_content(html, "https://example.com")
        assert result['data']['challenging']['tables'] == 1
        assert result['data']['challenging']['forms'] == 1
        assert result['data']['challenging']['images_without_alt'] == 1
    
    def test_inaccessible_content(self):
        html = '''<html><body>
            <canvas></canvas>
            <video src="test.mp4"></video>
            <div onclick="doSomething()">Click me</div>
        </body></html>'''
        result = extract_llm_readable_content(html, "https://example.com")
        assert result['data']['inaccessible']['canvas_elements'] == 1
        assert result['data']['inaccessible']['media_elements'] == 1
        assert result['data']['inaccessible']['javascript_dependent'] == 1


class TestDuplicateContent:
    
    def test_no_duplicates(self):
        pages_data = [
            {'url': 'https://example.com/page1', 'html': '<html><body><p>Unique content about cats</p></body></html>'},
            {'url': 'https://example.com/page2', 'html': '<html><body><p>Different content about dogs</p></body></html>'}
        ]
        result = detect_duplicate_content(pages_data)
        assert result['passed'] is True
        assert result['data']['total_duplicates'] == 0
    
    def test_insufficient_pages(self):
        pages_data = [
            {'url': 'https://example.com/page1', 'html': '<html><body><p>Content</p></body></html>'}
        ]
        result = detect_duplicate_content(pages_data)
        assert result['passed'] is True
        assert "Insufficient pages" in result['message']


class TestRecommendations:
    
    def test_generate_recommendations(self):
        page_results = [
            {
                'url': 'https://example.com',
                'checks': {
                    'robots': {'passed': False},
                    'h1': {'passed': True},
                    'structured_data_richness': {'passed': False}
                }
            }
        ]
        result = generate_llm_recommendations(page_results)
        assert len(result['critical']) > 0
        assert len(result['important']) > 0
        assert result['overall_score'] < 100
    
    def test_perfect_score_recommendations(self):
        page_results = [
            {
                'url': 'https://example.com',
                'checks': {
                    'robots': {'passed': True},
                    'h1': {'passed': True},
                    'structured_data_richness': {'passed': True}
                }
            }
        ]
        result = generate_llm_recommendations(page_results)
        assert result['overall_score'] == 100
