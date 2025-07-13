"""Unit tests for OpenAI reporter module."""

import pytest
from unittest.mock import Mock, patch
from llm_seo.openai_reporter import LLMReportGenerator, generate_report_with_openai
from llm_seo.llm_scraper import scrape_as_llm


class TestLLMReportGenerator:
    
    def test_init_with_api_key(self):
        generator = LLMReportGenerator("test-key")
        assert generator.client.api_key == "test-key"
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'})
    def test_init_with_env_key(self):
        generator = LLMReportGenerator()
        assert generator.client.api_key == "env-key"
    
    @patch('llm_seo.openai_reporter.OpenAI')
    def test_generate_report_success(self, mock_openai):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test report content"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = LLMReportGenerator("test-key")
        
        # Test data
        audit_results = {
            'site_score': 75,
            'pages': [{'url': 'https://example.com'}],
            'recommendations': {'critical': [], 'important': [], 'suggested': []},
            'llm_readiness_summary': {'accessibility_breakdown': {'high_accessibility': 1}}
        }
        
        pages_html_data = [
            {'url': 'https://example.com', 'html': '<html><body><h1>Test</h1></body></html>'}
        ]
        
        result = generator.generate_comprehensive_report(audit_results, pages_html_data)
        
        assert result['success'] is True
        assert result['report'] == "Test report content"
        assert 'scraped_content_summary' in result
        assert 'audit_summary' in result
    
    @patch('llm_seo.openai_reporter.OpenAI')
    def test_generate_report_failure(self, mock_openai):
        mock_openai.side_effect = Exception("API Error")
        
        generator = LLMReportGenerator("test-key")
        
        result = generator.generate_comprehensive_report({}, [])
        
        assert result['success'] is False
        assert "Failed to generate report" in result['error']
        assert result['report'] is None


class TestLLMScraper:
    
    def test_scrape_basic_content(self):
        html = '''<html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is a test paragraph with enough content to be meaningful.</p>
                <img src="test.jpg" alt="Test image">
            </body>
        </html>'''
        
        result = scrape_as_llm(html, "https://example.com")
        
        assert result['title'] == "Test Page"
        assert len(result['headings']) == 1
        assert result['headings'][0]['text'] == "Main Heading"
        assert "test paragraph" in result['main_content']
        assert len(result['images_with_context']) == 1
        assert result['llm_richness_score'] > 0
    
    def test_scrape_structured_data(self):
        html = '''<html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Test Article"
                }
                </script>
            </head>
            <body><p>Content</p></body>
        </html>'''
        
        result = scrape_as_llm(html, "https://example.com")
        
        assert len(result['structured_data']) == 1
        assert result['structured_data'][0]['@type'] == "Article"
    
    def test_scrape_error_handling(self):
        # Test with invalid HTML
        result = scrape_as_llm("invalid html", "https://example.com")
        
        # Should not crash and should return basic structure
        assert 'title' in result
        assert 'headings' in result
        assert 'main_content' in result


def test_generate_report_convenience_function():
    with patch('llm_seo.openai_reporter.LLMReportGenerator') as mock_generator_class:
        mock_generator = Mock()
        mock_generator.generate_comprehensive_report.return_value = {"success": True}
        mock_generator_class.return_value = mock_generator
        
        result = generate_report_with_openai({}, [], "test-key")
        
        mock_generator_class.assert_called_once_with("test-key")
        mock_generator.generate_comprehensive_report.assert_called_once()
        assert result == {"success": True}
