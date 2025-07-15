"""OpenAI-powered report generation for LLM-SEO analysis."""

import os
import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def generate_report_with_openai(audit_results, pages_html_data):
    """Generate a comprehensive report using OpenAI with web search capabilities."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"DEBUG: OpenAI function called, API key present: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("DEBUG: No OpenAI API key found in environment")
        return {
            'success': False,
            'error': 'OpenAI API key not found in environment variables'
        }
    
    try:
        print("DEBUG: Creating OpenAI client...")
        client = openai.OpenAI(api_key=api_key)
        
        # Get the main website URL from the first page
        main_url = pages_html_data[0]['url'] if pages_html_data else "the website"
        
        # Create prompt for AI to actually visit and analyze the website
        print("DEBUG: Creating web analysis prompt...")
        prompt = create_web_analysis_prompt(audit_results, main_url)
        
        # Generate report using search-enabled model
        print("DEBUG: Calling OpenAI API with search capabilities...")
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": "You are an expert SEO and LLM optimization consultant with web browsing capabilities. Visit the website and provide detailed, actionable analysis based on what you can actually see."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        print("DEBUG: OpenAI API call successful!")
        return {
            'success': True,
            'report': response.choices[0].message.content,
            'scraped_content_summary': {'analysis_type': 'live_web_analysis'}
        }
        
    except Exception as e:
        print(f"DEBUG: OpenAI API error: {str(e)}")
        return {
            'success': False,
            'error': f'OpenAI API error: {str(e)}'
        }


def extract_content_for_llm(pages_html_data):
    """Extract content as an LLM would see it."""
    
    content_summary = {
        'total_pages': len(pages_html_data),
        'pages': []
    }
    
    for page in pages_html_data[:5]:  # Limit to first 5 pages
        soup = BeautifulSoup(page['html'], 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract key elements
        title = soup.find('title')
        h1 = soup.find('h1')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        
        # Get main content (first 500 chars)
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        page_summary = {
            'url': page['url'],
            'title': title.get_text() if title else 'No title',
            'h1': h1.get_text() if h1 else 'No H1',
            'meta_description': meta_desc.get('content') if meta_desc else 'No meta description',
            'content_preview': clean_text[:500] + '...' if len(clean_text) > 500 else clean_text,
            'content_length': len(clean_text)
        }
        
        content_summary['pages'].append(page_summary)
    
    return content_summary


def create_web_analysis_prompt(audit_results, main_url):
    """Create analysis prompt for AI to visit and analyze the website."""
    
    prompt = f"""
Please visit and analyze the website: {main_url}

I need you to actually browse this website and provide a comprehensive LLM readiness analysis based on what you can see when you visit it.

TECHNICAL AUDIT CONTEXT:
- Overall Score: {audit_results.get('site_score', 0)}/100
- Pages Analyzed: {len(audit_results.get('pages', []))}
- Critical Issues: {len(audit_results.get('recommendations', {}).get('critical', []))}
- Important Issues: {len(audit_results.get('recommendations', {}).get('important', []))}

PLEASE VISIT THE WEBSITE AND ANALYZE:

1. **WHAT AI CAN ACTUALLY SEE**: Browse the main pages and describe what content is visible and accessible to AI systems. Be specific about:
   - The business/organization and what they do
   - Main services or products offered
   - Key information that would help AI assistants answer user questions
   - Content structure and organization

2. **CONTENT GAPS FOR AI**: Based on your actual visit, what important information is missing that would help AI understand this website better?

3. **WEBSITE-SPECIFIC RECOMMENDATIONS**: Provide 5-8 specific, actionable recommendations for THIS website based on what you actually see. Reference specific pages, content, or elements you observe. For example:
   - "The homepage shows [specific content] but lacks [specific missing element]"
   - "The about page mentions [specific service] but should include [specific improvement]"

4. **LLM OPTIMIZATION PRIORITIES**: What are the top 3 most critical changes needed for better AI understanding, based on your actual analysis of the live website?

Please provide concrete, specific recommendations based on your actual visit to the website, not generic SEO advice.
"""
    
    return prompt


def format_content_sample(content_summary):
    """Format content sample for prompt."""
    
    sample = ""
    for page in content_summary['pages'][:3]:  # First 3 pages
        sample += f"""
Page: {page['url']}
Title: {page['title']}
H1: {page['h1']}
Meta Description: {page['meta_description']}
Content Preview: {page['content_preview'][:200]}...
---
"""
    
    return sample
