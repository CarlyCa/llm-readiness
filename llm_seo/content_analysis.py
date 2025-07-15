"""Content analysis for LLM readiness."""

import json
import re
import textstat
from bs4 import BeautifulSoup


def analyze_content_readability(page_data):
    """Analyze content readability using Flesch-Kincaid."""
    
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    if len(text) < 100:
        return 0
    
    try:
        # Flesch Reading Ease (0-100, higher is better)
        flesch_score = textstat.flesch_reading_ease(text)
        
        # Convert to 0-100 scale where 100 is best
        if flesch_score >= 90:
            return 100
        elif flesch_score >= 80:
            return 90
        elif flesch_score >= 70:
            return 80
        elif flesch_score >= 60:
            return 70
        elif flesch_score >= 50:
            return 60
        elif flesch_score >= 30:
            return 50
        else:
            return 30
            
    except:
        return 50  # Default score if analysis fails


def analyze_structured_data(page_data):
    """Analyze structured data richness."""
    
    soup = BeautifulSoup(page_data['html'], 'html.parser')
    
    schema_count = 0
    richness_score = 0
    
    # Check for JSON-LD
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            schema_count += 1
            richness_score += 20  # 20 points per JSON-LD schema
        except:
            continue
    
    # Check for microdata
    microdata_items = soup.find_all(attrs={'itemtype': True})
    if microdata_items:
        schema_count += len(microdata_items)
        richness_score += len(microdata_items) * 10  # 10 points per microdata item
    
    # Check for RDFa
    rdfa_items = soup.find_all(attrs={'typeof': True})
    if rdfa_items:
        schema_count += len(rdfa_items)
        richness_score += len(rdfa_items) * 10  # 10 points per RDFa item
    
    # Check for Open Graph
    og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
    if og_tags:
        richness_score += min(len(og_tags) * 2, 20)  # Up to 20 points for OG tags
    
    # Check for Twitter Cards
    twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
    if twitter_tags:
        richness_score += min(len(twitter_tags) * 2, 10)  # Up to 10 points for Twitter cards
    
    return {
        'schema_count': schema_count,
        'richness_score': min(richness_score, 100)  # Cap at 100
    }
