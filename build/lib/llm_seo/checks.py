"""Website audit checks for LLM readiness."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json


def check_robots(url):
    """Check robots.txt for GPTBot and general bot permissions."""
    try:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        response = requests.get(robots_url, timeout=10)
        if response.status_code != 200:
            return {"passed": False, "message": "robots.txt not found"}
        
        robots_content = response.text.lower()
        
        # Check for GPTBot specifically
        gptbot_allowed = True
        if "user-agent: gptbot" in robots_content:
            # Look for disallow rules for GPTBot
            lines = robots_content.split('\n')
            in_gptbot_section = False
            for line in lines:
                line = line.strip()
                if line.startswith("user-agent: gptbot"):
                    in_gptbot_section = True
                elif line.startswith("user-agent:") and "gptbot" not in line:
                    in_gptbot_section = False
                elif in_gptbot_section and line.startswith("disallow: /"):
                    gptbot_allowed = False
                    break
        
        # Check for general bot permissions
        general_allowed = "disallow: /" not in robots_content or "user-agent: *" not in robots_content
        
        if gptbot_allowed and general_allowed:
            return {"passed": True, "message": "Robots.txt allows bot access"}
        else:
            return {"passed": False, "message": "Robots.txt blocks bot access"}
            
    except Exception as e:
        return {"passed": False, "message": f"Error checking robots.txt: {str(e)}"}


def check_meta_robots(html):
    """Check for meta robots tags that might block indexing."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        
        if not meta_robots:
            return {"passed": True, "message": "No restrictive meta robots tag found"}
        
        content = meta_robots.get('content', '').lower()
        
        if 'noindex' in content or 'nofollow' in content:
            return {"passed": False, "message": f"Meta robots restricts indexing: {content}"}
        
        return {"passed": True, "message": "Meta robots allows indexing"}
        
    except Exception as e:
        return {"passed": False, "message": f"Error checking meta robots: {str(e)}"}


def check_h1(html):
    """Ensure there's at least one H1 tag."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        h1_tags = soup.find_all('h1')
        
        if not h1_tags:
            return {"passed": False, "message": "No H1 tags found"}
        
        # Check if H1 has meaningful content
        h1_text = h1_tags[0].get_text(strip=True)
        if not h1_text:
            return {"passed": False, "message": "H1 tag is empty"}
        
        return {"passed": True, "message": f"Found H1: '{h1_text[:50]}{'...' if len(h1_text) > 50 else ''}'"}
        
    except Exception as e:
        return {"passed": False, "message": f"Error checking H1: {str(e)}"}


def check_alt_text(html):
    """Verify all img tags have non-empty alt attributes."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        img_tags = soup.find_all('img')
        
        if not img_tags:
            return {"passed": True, "message": "No images found"}
        
        missing_alt = []
        empty_alt = []
        
        for img in img_tags:
            src = img.get('src', 'unknown')
            alt = img.get('alt')
            
            if alt is None:
                missing_alt.append(src)
            elif not alt.strip():
                empty_alt.append(src)
        
        if missing_alt or empty_alt:
            issues = []
            if missing_alt:
                issues.append(f"{len(missing_alt)} images missing alt text")
            if empty_alt:
                issues.append(f"{len(empty_alt)} images with empty alt text")
            
            return {"passed": False, "message": "; ".join(issues)}
        
        return {"passed": True, "message": f"All {len(img_tags)} images have alt text"}
        
    except Exception as e:
        return {"passed": False, "message": f"Error checking alt text: {str(e)}"}


def check_jsonld(html):
    """Find JSON-LD structured data."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        
        if not jsonld_scripts:
            return {"passed": False, "message": "No JSON-LD structured data found"}
        
        valid_jsonld = []
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type'):
                    valid_jsonld.append(data.get('@type'))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type'):
                            valid_jsonld.append(item.get('@type'))
            except json.JSONDecodeError:
                continue
        
        if valid_jsonld:
            return {"passed": True, "message": f"Found JSON-LD types: {', '.join(set(valid_jsonld))}"}
        else:
            return {"passed": False, "message": "JSON-LD scripts found but invalid or empty"}
            
    except Exception as e:
        return {"passed": False, "message": f"Error checking JSON-LD: {str(e)}"}
