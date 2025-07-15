"""LLM-like content scraper that extracts content as an LLM bot would see it."""

import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def scrape_as_llm(html, url):
    """Extract content exactly as an LLM would see and process it."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove elements that LLMs typically can't access
        for element in soup(['script', 'style', 'noscript', 'iframe', 'canvas', 'svg']):
            element.decompose()
        
        # Extract structured content that LLMs prioritize
        llm_content = {
            "title": "",
            "headings": [],
            "main_content": "",
            "structured_data": [],
            "images_with_context": [],
            "links_with_context": [],
            "tables_content": [],
            "lists_content": [],
            "metadata": {}
        }
        
        # Title (highest priority for LLMs)
        title_tag = soup.find('title')
        if title_tag:
            llm_content["title"] = title_tag.get_text().strip()
        
        # Meta description (important for LLM understanding)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            llm_content["metadata"]["description"] = meta_desc.get('content', '').strip()
        
        # Headings (critical for LLM content structure understanding)
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            text = heading.get_text().strip()
            if text:
                llm_content["headings"].append({
                    "level": level,
                    "text": text
                })
        
        # Main content extraction (what LLMs focus on)
        # Remove navigation, footer, sidebar elements
        for element in soup(['nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # Extract paragraphs and main text
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                paragraphs.append(text)
        
        llm_content["main_content"] = "\n\n".join(paragraphs)
        
        # Structured data (JSON-LD) - highly valuable for LLMs
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string)
                llm_content["structured_data"].append(data)
            except json.JSONDecodeError:
                continue
        
        # Images with alt text (accessible to LLMs)
        for img in soup.find_all('img'):
            alt_text = img.get('alt', '').strip()
            src = img.get('src', '')
            if alt_text:  # Only include images with alt text
                # Get surrounding context
                context = ""
                parent = img.parent
                if parent:
                    context = parent.get_text().strip()[:200]
                
                llm_content["images_with_context"].append({
                    "alt_text": alt_text,
                    "src": src,
                    "context": context
                })
        
        # Links with context (LLMs can understand link relationships)
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            link_text = link.get_text().strip()
            if link_text and href:
                # Resolve relative URLs
                full_url = urljoin(url, href)
                
                # Get surrounding context
                context = ""
                parent = link.parent
                if parent:
                    context = parent.get_text().strip()[:200]
                
                llm_content["links_with_context"].append({
                    "text": link_text,
                    "url": full_url,
                    "context": context
                })
        
        # Tables (challenging but parseable by LLMs)
        for table in soup.find_all('table'):
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                if any(row_data):  # Only include non-empty rows
                    table_data.append(row_data)
            
            if table_data:
                llm_content["tables_content"].append(table_data)
        
        # Lists (well-structured for LLMs)
        for list_elem in soup.find_all(['ul', 'ol']):
            list_items = []
            for li in list_elem.find_all('li'):
                item_text = li.get_text().strip()
                if item_text:
                    list_items.append(item_text)
            
            if list_items:
                list_type = "ordered" if list_elem.name == 'ol' else "unordered"
                llm_content["lists_content"].append({
                    "type": list_type,
                    "items": list_items
                })
        
        # Calculate content richness score for LLMs
        richness_score = calculate_llm_content_richness(llm_content)
        llm_content["llm_richness_score"] = richness_score
        
        return llm_content
        
    except Exception as e:
        return {
            "error": f"Failed to scrape content as LLM: {str(e)}",
            "title": "",
            "headings": [],
            "main_content": "",
            "structured_data": [],
            "images_with_context": [],
            "links_with_context": [],
            "tables_content": [],
            "lists_content": [],
            "metadata": {},
            "llm_richness_score": 0
        }


def analyze_llm_accessibility(html, url):
    """Detailed analysis of what LLMs can and cannot access on a page."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        accessibility_report = {
            "accessible_content": {
                "text_elements": [],
                "structured_data": [],
                "semantic_elements": [],
                "accessible_media": []
            },
            "challenging_content": {
                "complex_structures": [],
                "interactive_elements": [],
                "partially_accessible": []
            },
            "inaccessible_content": {
                "visual_only": [],
                "javascript_dependent": [],
                "multimedia_without_text": [],
                "embedded_content": []
            },
            "recommendations": []
        }
        
        # ACCESSIBLE CONTENT ANALYSIS
        
        # Text elements LLMs can easily read
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            text = heading.get_text().strip()
            if text:
                accessibility_report["accessible_content"]["text_elements"].append({
                    "type": f"Heading {heading.name.upper()}",
                    "content": text[:100] + "..." if len(text) > 100 else text
                })
        
        # Paragraphs and text content
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:  # Limit to first 5 for brevity
            text = p.get_text().strip()
            if text and len(text) > 20:
                accessibility_report["accessible_content"]["text_elements"].append({
                    "type": "Paragraph",
                    "content": text[:100] + "..." if len(text) > 100 else text
                })
        
        # Lists
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            if items:
                list_type = "Ordered List" if list_elem.name == 'ol' else "Unordered List"
                accessibility_report["accessible_content"]["text_elements"].append({
                    "type": list_type,
                    "content": f"{len(items)} items"
                })
        
        # Structured data
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string)
                schema_type = data.get('@type', 'Unknown') if isinstance(data, dict) else 'Multiple schemas'
                accessibility_report["accessible_content"]["structured_data"].append({
                    "type": "JSON-LD Schema",
                    "schema_type": schema_type
                })
            except json.JSONDecodeError:
                continue
        
        # Semantic elements
        semantic_elements = soup.find_all(['article', 'section', 'main', 'aside'])
        for elem in semantic_elements:
            accessibility_report["accessible_content"]["semantic_elements"].append({
                "type": f"Semantic {elem.name}",
                "content": f"Contains {len(elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']))} text elements"
            })
        
        # Images with alt text
        images_with_alt = soup.find_all('img', alt=True)
        for img in images_with_alt:
            alt_text = img.get('alt', '').strip()
            if alt_text:
                accessibility_report["accessible_content"]["accessible_media"].append({
                    "type": "Image with alt text",
                    "alt_text": alt_text[:100] + "..." if len(alt_text) > 100 else alt_text,
                    "src": img.get('src', 'No source')[:50]
                })
        
        # CHALLENGING CONTENT ANALYSIS
        
        # Tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            accessibility_report["challenging_content"]["complex_structures"].append({
                "type": "Table",
                "details": f"{len(rows)} rows, may be difficult for LLMs to parse correctly"
            })
        
        # Forms
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'select', 'textarea'])
            accessibility_report["challenging_content"]["interactive_elements"].append({
                "type": "Form",
                "details": f"{len(inputs)} input fields, LLMs cannot interact"
            })
        
        # Images without alt text
        images_no_alt = soup.find_all('img')
        images_no_alt = [img for img in images_no_alt if not img.get('alt')]
        for img in images_no_alt:
            accessibility_report["challenging_content"]["partially_accessible"].append({
                "type": "Image without alt text",
                "details": f"Visual content not described: {img.get('src', 'No source')[:50]}"
            })
        
        # INACCESSIBLE CONTENT ANALYSIS
        
        # Canvas elements
        canvas_elements = soup.find_all('canvas')
        for canvas in canvas_elements:
            accessibility_report["inaccessible_content"]["visual_only"].append({
                "type": "Canvas element",
                "details": "Dynamic visual content, completely inaccessible to LLMs"
            })
        
        # SVG without text
        svg_elements = soup.find_all('svg')
        for svg in svg_elements:
            text_content = svg.get_text().strip()
            if not text_content:
                accessibility_report["inaccessible_content"]["visual_only"].append({
                    "type": "SVG graphic",
                    "details": "Vector graphics without text description"
                })
        
        # Audio/Video without transcripts
        media_elements = soup.find_all(['audio', 'video'])
        for media in media_elements:
            accessibility_report["inaccessible_content"]["multimedia_without_text"].append({
                "type": f"{media.name.title()} element",
                "details": "Audio/visual content, LLMs cannot process media files"
            })
        
        # JavaScript-dependent content
        js_dependent = soup.find_all(attrs={"onclick": True})
        js_dependent.extend(soup.find_all(attrs={"onload": True}))
        for elem in js_dependent:
            accessibility_report["inaccessible_content"]["javascript_dependent"].append({
                "type": f"{elem.name.title()} with JavaScript",
                "details": "Requires JavaScript execution, not accessible to LLMs"
            })
        
        # iFrames
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', 'No source')
            accessibility_report["inaccessible_content"]["embedded_content"].append({
                "type": "iFrame",
                "details": f"Embedded content from: {src[:50]}"
            })
        
        # GENERATE RECOMMENDATIONS
        
        if len(images_no_alt) > 0:
            accessibility_report["recommendations"].append(f"Add alt text to {len(images_no_alt)} images for LLM accessibility")
        
        if len(jsonld_scripts) == 0:
            accessibility_report["recommendations"].append("Add structured data (JSON-LD) to help LLMs understand content context")
        
        if len(headings) == 0:
            accessibility_report["recommendations"].append("Add heading structure (H1-H6) to improve content hierarchy for LLMs")
        
        if len(tables) > 0:
            accessibility_report["recommendations"].append(f"Consider converting {len(tables)} tables to simpler list formats for better LLM comprehension")
        
        if len(media_elements) > 0:
            accessibility_report["recommendations"].append(f"Provide text descriptions or transcripts for {len(media_elements)} media elements")
        
        return accessibility_report
        
    except Exception as e:
        return {
            "error": f"Failed to analyze LLM accessibility: {str(e)}",
            "accessible_content": {},
            "challenging_content": {},
            "inaccessible_content": {},
            "recommendations": []
        }


def calculate_llm_content_richness(content):
    """Calculate how rich and accessible the content is for LLMs."""
    score = 0
    
    # Title presence and quality
    if content["title"]:
        score += 10
        if len(content["title"]) > 10:
            score += 5
    
    # Heading structure
    if content["headings"]:
        score += len(content["headings"]) * 3
        # Bonus for proper heading hierarchy
        h1_count = sum(1 for h in content["headings"] if h["level"] == 1)
        if h1_count == 1:  # Exactly one H1 is ideal
            score += 10
    
    # Main content quality
    if content["main_content"]:
        word_count = len(content["main_content"].split())
        if word_count > 100:
            score += 15
        if word_count > 500:
            score += 10
        if word_count > 1000:
            score += 5
    
    # Structured data (highly valuable for LLMs)
    score += len(content["structured_data"]) * 15
    
    # Images with alt text
    score += len(content["images_with_context"]) * 2
    
    # Well-structured lists
    score += len(content["lists_content"]) * 3
    
    # Metadata presence
    if content["metadata"].get("description"):
        score += 8
    
    return min(100, score)


def extract_key_topics(content):
    """Extract key topics and themes that an LLM would identify."""
    topics = []
    
    # Extract from title
    if content["title"]:
        topics.append(f"Page Title: {content['title']}")
    
    # Extract from headings
    if content["headings"]:
        h1_headings = [h["text"] for h in content["headings"] if h["level"] == 1]
        if h1_headings:
            topics.append(f"Main Topic: {h1_headings[0]}")
        
        h2_headings = [h["text"] for h in content["headings"] if h["level"] == 2]
        if h2_headings:
            topics.append(f"Subtopics: {', '.join(h2_headings[:3])}")
    
    # Extract from structured data
    for schema in content["structured_data"]:
        if isinstance(schema, dict):
            schema_type = schema.get("@type", "")
            if schema_type:
                topics.append(f"Content Type: {schema_type}")
            
            # Extract specific fields based on schema type
            if schema_type == "Article" and schema.get("headline"):
                topics.append(f"Article: {schema['headline']}")
            elif schema_type == "Product" and schema.get("name"):
                topics.append(f"Product: {schema['name']}")
            elif schema_type == "FAQPage":
                topics.append("Content Type: FAQ/Questions & Answers")
    
    return topics
