"""Web crawler for fetching pages and extracting internal links."""

import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .checks import check_robots, check_meta_robots, check_h1, check_alt_text, check_jsonld


class RateLimiter:
    """Simple rate limiter to avoid overwhelming servers."""
    
    def __init__(self, delay=1.0):
        self.delay = delay
        self.last_request = 0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()


def get_internal_links(html, base_url):
    """Extract internal links from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(base_url).netloc
    links = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Only include internal links (same domain)
        if parsed.netloc == base_domain and parsed.scheme in ['http', 'https']:
            # Remove fragment and query parameters for deduplication
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            links.add(clean_url)
    
    return list(links)


def fetch_page(url, rate_limiter):
    """Fetch a single page with error handling."""
    try:
        rate_limiter.wait()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; LLM-SEO-Auditor/1.0)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return {
            'url': url,
            'html': response.text,
            'status_code': response.status_code,
            'error': None
        }
        
    except Exception as e:
        return {
            'url': url,
            'html': None,
            'status_code': None,
            'error': str(e)
        }


def run_checks_on_page(page_data):
    """Run all checks on a single page."""
    url = page_data['url']
    html = page_data['html']
    
    if page_data['error'] or not html:
        return {
            'url': url,
            'checks': {
                'robots': {'passed': False, 'message': f"Failed to fetch page: {page_data['error']}"},
                'meta_robots': {'passed': False, 'message': 'Page not accessible'},
                'h1': {'passed': False, 'message': 'Page not accessible'},
                'alt_text': {'passed': False, 'message': 'Page not accessible'},
                'jsonld': {'passed': False, 'message': 'Page not accessible'}
            },
            'score': 0
        }
    
    checks = {
        'robots': check_robots(url),
        'meta_robots': check_meta_robots(html),
        'h1': check_h1(html),
        'alt_text': check_alt_text(html),
        'jsonld': check_jsonld(html)
    }
    
    # Calculate page score
    passed_checks = sum(1 for check in checks.values() if check['passed'])
    score = int((passed_checks / len(checks)) * 100)
    
    return {
        'url': url,
        'checks': checks,
        'score': score
    }


def crawl_site(start_url, max_depth=1):
    """Crawl a site up to the specified depth."""
    rate_limiter = RateLimiter(delay=1.0)
    visited = set()
    to_visit = [(start_url, 0)]  # (url, depth)
    results = []
    
    while to_visit:
        url, depth = to_visit.pop(0)
        
        if url in visited or depth > max_depth:
            continue
            
        visited.add(url)
        
        # Fetch the page
        page_data = fetch_page(url, rate_limiter)
        
        # Run checks on the page
        page_result = run_checks_on_page(page_data)
        results.append(page_result)
        
        # Extract links for next depth level
        if depth < max_depth and page_data['html']:
            internal_links = get_internal_links(page_data['html'], url)
            for link in internal_links:
                if link not in visited:
                    to_visit.append((link, depth + 1))
    
    return results
