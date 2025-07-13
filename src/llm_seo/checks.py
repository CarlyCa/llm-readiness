"""LLM-SEO audit checks module."""

import re
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests


def check_robots_txt_allows_crawling(page_data):
    """Check if robots.txt allows crawling."""
    url = page_data['url']
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    
    try:
        robots_url = urljoin(base_url, '/robots.txt')
        response = requests.get(robots_url, timeout=10)
        
        # Per RFC: 404 means no restrictions (implicit allow)
        if response.status_code == 404:
            return {'passed': True, 'message': 'No robots.txt found (allows crawling per RFC)'}
        
        if response.status_code != 200:
            # Other non-200 codes also treated as no restrictions
            return {'passed': True, 'message': f'robots.txt returned {response.status_code} (allows crawling)'}
        
        robots_content = response.text.lower()
        
        # Check for complete blocking: User-agent: * with Disallow: / (and nothing else significant)
        lines = [line.strip() for line in robots_content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        # Look for User-agent: * section
        in_wildcard_section = False
        wildcard_disallows = []
        
        for line in lines:
            if line.startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                in_wildcard_section = (agent == '*')
            elif in_wildcard_section and line.startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                wildcard_disallows.append(path)
            elif line.startswith('user-agent:') and in_wildcard_section:
                # End of wildcard section
                break
        
        # Only flag as blocked if there's a complete block (Disallow: / with no other significant allows)
        if '/' in wildcard_disallows and len([d for d in wildcard_disallows if d == '/']) > 0:
            # Check if there are any Allow rules that might override
            allows = [line for line in lines if line.startswith('allow:')]
            if not allows:
                return {'passed': False, 'message': 'robots.txt disallows all crawling'}
        
        # Don't flag AI bot listings as blocking - they're just preferences
        # Most AI systems can still access the content despite being listed
        return {'passed': True, 'message': 'robots.txt allows crawling'}
        
    except Exception as e:
        # Network errors also treated as no restrictions
        return {'passed': True, 'message': f'Could not check robots.txt (allows crawling): {str(e)}'}


def check_meta_robots_allows_indexing(page_data):
    """Check if meta robots allows indexing."""
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    meta_robots = soup.find('meta', attrs={'name': re.compile(r'^robots$', re.I)})
    
    if not meta_robots:
        return {'passed': True, 'message': 'No meta robots tag (allows indexing)'}
    
    content = meta_robots.get('content', '').lower()
    
    if 'noindex' in content:
        return {'passed': False, 'message': 'Meta robots contains noindex'}
    
    return {'passed': True, 'message': 'Meta robots allows indexing'}


def check_has_h1_tag(page_data):
    """Check if page has H1 tag or equivalent heading structure."""
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    h1_tags = soup.find_all('h1')
    
    if h1_tags:
        if len(h1_tags) > 1:
            return {'passed': False, 'message': f'Multiple H1 tags found ({len(h1_tags)}), should have exactly one'}
        
        h1_text = h1_tags[0].get_text(strip=True)
        if not h1_text:
            return {'passed': False, 'message': 'H1 tag is empty'}
        
        return {'passed': True, 'message': f'H1 tag found: "{h1_text[:50]}..."'}
    
    # Check for Squarespace-style headings (often use H2 as main heading)
    h2_tags = soup.find_all('h2')
    if h2_tags:
        # Look for H2 that might be the main page title
        for h2 in h2_tags:
            h2_text = h2.get_text(strip=True)
            # Check if it's likely a main heading (not navigation, etc.)
            if len(h2_text) > 10 and not any(nav_word in h2_text.lower() for nav_word in ['menu', 'navigation', 'skip to']):
                return {'passed': False, 'message': f'No H1 found, but H2 could be main heading: "{h2_text[:50]}..." - Consider changing to H1 for better SEO'}
    
    return {'passed': False, 'message': 'No H1 tag found - Add a clear main heading for better AI understanding'}


def check_has_meta_description(page_data):
    """Check if page has meta description."""
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    meta_desc = soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)})
    
    if not meta_desc:
        return {'passed': False, 'message': 'No meta description found'}
    
    content = meta_desc.get('content', '').strip()
    
    if not content:
        return {'passed': False, 'message': 'Meta description is empty'}
    
    if len(content) < 120:
        return {'passed': False, 'message': f'Meta description too short ({len(content)} chars, recommend 120-160)'}
    
    if len(content) > 160:
        return {'passed': False, 'message': f'Meta description too long ({len(content)} chars, recommend 120-160)'}
    
    return {'passed': True, 'message': f'Good meta description ({len(content)} chars)'}


def check_images_have_alt_text(page_data):
    """Check if images have alt text."""
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    images = soup.find_all('img')
    
    if not images:
        return {'passed': True, 'message': 'No images found'}
    
    missing_alt = []
    empty_alt = []
    
    for img in images:
        src = img.get('src', '')
        alt = img.get('alt')
        
        if alt is None:
            missing_alt.append(src)
        elif not alt.strip():
            empty_alt.append(src)
    
    total_issues = len(missing_alt) + len(empty_alt)
    
    if total_issues == 0:
        return {'passed': True, 'message': f'All {len(images)} images have alt text'}
    
    if total_issues == len(images):
        return {'passed': False, 'message': f'All {len(images)} images missing alt text'}
    
    return {'passed': False, 'message': f'{total_issues}/{len(images)} images missing/empty alt text'}
