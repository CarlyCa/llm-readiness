"""Web crawler for LLM-SEO analysis."""

import requests
import time
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup


def crawl_site(start_url, max_depth=1):
    """Crawl a website starting from the given URL."""
    
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url
    
    visited = set()
    to_visit = [(start_url, 0)]
    pages_data = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; LLM-SEO-Bot/1.0; +https://example.com/bot)'
    }
    
    while to_visit and len(pages_data) < 50:  # Limit to 50 pages
        url, depth = to_visit.pop(0)
        
        # Normalize URL by removing fragment identifier (#page, etc.)
        normalized_url, fragment = urldefrag(url)
        
        if normalized_url in visited or depth > max_depth:
            continue
            
        visited.add(normalized_url)
        
        try:
            print(f"Crawling: {normalized_url} (depth {depth})")
            response = requests.get(normalized_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            page_data = {
                'url': normalized_url,
                'html': response.text,
                'status_code': response.status_code,
                'depth': depth
            }
            
            pages_data.append(page_data)
            
            # Find links for next depth level
            if depth < max_depth:
                soup = BeautifulSoup(response.text, 'html.parser')
                base_domain = urlparse(normalized_url).netloc
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(normalized_url, href)
                    
                    # Normalize the discovered URL too
                    normalized_full_url, _ = urldefrag(full_url)
                    
                    # Only follow links on same domain
                    if urlparse(normalized_full_url).netloc == base_domain:
                        if normalized_full_url not in visited:
                            to_visit.append((normalized_full_url, depth + 1))
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error crawling {normalized_url}: {str(e)}")
            continue
    
    return pages_data
