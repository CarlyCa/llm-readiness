"""OpenAI-powered website scraper that analyzes content as an AI would see it."""

import os
import openai
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
try:
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass


def scrape_website_with_openai(pages_data):
    """Use OpenAI to analyze what AI can see on the website and provide insights."""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {
            'success': False,
            'error': 'OpenAI API key required for AI-powered analysis',
            'ai_visible_content': {},
            'website_specific_recommendations': []
        }
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Extract content from pages for AI analysis
        website_content = extract_website_content(pages_data)
        
        # Create prompt for AI to analyze what it can see
        prompt = create_ai_analysis_prompt(website_content)
        
        # Get AI analysis
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant analyzing a website from the perspective of what AI systems can access and understand. Provide specific, actionable insights based on the actual content you can see."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        ai_analysis = response.choices[0].message.content
        
        # Parse AI response into structured data
        structured_analysis = parse_ai_analysis(ai_analysis, website_content)
        
        return {
            'success': True,
            'ai_analysis': ai_analysis,
            'ai_visible_content': structured_analysis['visible_content'],
            'website_specific_recommendations': structured_analysis['recommendations'],
            'content_summary': website_content
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'OpenAI analysis failed: {str(e)}',
            'ai_visible_content': {},
            'website_specific_recommendations': []
        }


def extract_website_content(pages_data):
    """Extract key content from website pages for AI analysis."""
    
    website_content = {
        'domain': '',
        'total_pages': len(pages_data),
        'pages': []
    }
    
    for page in pages_data:
        if not page.get('html'):
            continue
            
        soup = BeautifulSoup(page['html'], 'html.parser')
        
        # Extract domain from first page
        if not website_content['domain'] and page.get('url'):
            website_content['domain'] = urlparse(page['url']).netloc
        
        # Remove scripts, styles, etc.
        for element in soup(['script', 'style', 'noscript', 'iframe']):
            element.decompose()
        
        # Extract key elements
        title = soup.find('title')
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        images = soup.find_all('img')
        
        # Get main content (first 1000 chars)
        text_content = soup.get_text()
        clean_text = ' '.join(text_content.split())
        
        page_content = {
            'url': page['url'],
            'title': title.get_text().strip() if title else 'No title',
            'h1_headings': [h1.get_text().strip() for h1 in h1_tags if h1.get_text().strip()],
            'h2_headings': [h2.get_text().strip() for h2 in h2_tags if h2.get_text().strip()][:5],  # First 5 H2s
            'meta_description': meta_desc.get('content').strip() if meta_desc else 'No meta description',
            'main_content': clean_text[:1000] + '...' if len(clean_text) > 1000 else clean_text,
            'images_count': len(images),
            'images_with_alt': len([img for img in images if img.get('alt')]),
            'content_length': len(clean_text)
        }
        
        website_content['pages'].append(page_content)
    
    return website_content


def create_ai_analysis_prompt(website_content):
    """Create prompt for AI to analyze the website content."""
    
    domain = website_content['domain']
    pages = website_content['pages']
    
    prompt = f"""
I need you to analyze the website "{domain}" from the perspective of what AI systems like ChatGPT, Claude, and other LLMs can actually see and understand.

WEBSITE CONTENT ANALYSIS:
Domain: {domain}
Total Pages: {len(pages)}

PAGE DETAILS:
"""
    
    for i, page in enumerate(pages[:3], 1):  # Analyze first 3 pages
        prompt += f"""
Page {i}: {page['url']}
- Title: {page['title']}
- H1 Headings: {', '.join(page['h1_headings']) if page['h1_headings'] else 'None found'}
- H2 Headings: {', '.join(page['h2_headings']) if page['h2_headings'] else 'None found'}
- Meta Description: {page['meta_description']}
- Content Preview: {page['main_content'][:300]}...
- Images: {page['images_count']} total, {page['images_with_alt']} with descriptions

"""
    
    prompt += f"""
ANALYSIS REQUIRED:

1. WHAT AI CAN SEE: Based on the actual content above, what can AI systems easily understand about this website? Be specific about the business, services, or purpose.

2. CONTENT GAPS: What important information is missing that would help AI understand this website better?

3. WEBSITE-SPECIFIC RECOMMENDATIONS: Provide 5 specific, actionable recommendations for THIS website (not generic advice). Reference actual content, headings, or pages you see. For example:
   - "Add an H1 heading to the homepage like 'Professional Psychology Services in [City]' instead of the current title"
   - "The 'About' page mentions [specific service] but lacks a clear description for AI to understand"

4. IMMEDIATE FIXES: What are the top 3 most critical issues that prevent AI from understanding this specific website?

Be specific and reference actual content you can see. Don't give generic SEO advice.
"""
    
    return prompt


def parse_ai_analysis(ai_analysis, website_content):
    """Parse AI analysis into structured data."""
    
    # Extract visible content summary
    visible_content = {
        'business_type': 'Unknown',
        'main_services': [],
        'key_topics': [],
        'content_quality': 'Unknown',
        'ai_understanding_level': 'Low'
    }
    
    # Extract website-specific recommendations
    recommendations = []
    
    # Simple parsing - look for numbered lists or bullet points
    lines = ai_analysis.split('\n')
    current_section = ''
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identify sections
        if 'WHAT AI CAN SEE' in line.upper():
            current_section = 'visible'
        elif 'RECOMMENDATIONS' in line.upper() or 'FIXES' in line.upper():
            current_section = 'recommendations'
        elif line.startswith(('-', '•', '*')) or line[0].isdigit():
            if current_section == 'recommendations':
                # Clean up the recommendation
                rec = line.lstrip('-•*0123456789. ').strip()
                if len(rec) > 20:  # Only substantial recommendations
                    recommendations.append(rec)
    
    # If no structured recommendations found, extract from full text
    if not recommendations:
        # Look for sentences that contain action words
        sentences = ai_analysis.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['add', 'create', 'improve', 'change', 'include', 'should']):
                rec = sentence.strip()
                if len(rec) > 30 and len(rec) < 200:
                    recommendations.append(rec)
    
    return {
        'visible_content': visible_content,
        'recommendations': recommendations[:8]  # Limit to 8 recommendations
    }
