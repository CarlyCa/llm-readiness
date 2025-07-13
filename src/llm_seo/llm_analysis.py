"""Advanced LLM-specific content analysis and extraction."""

import re
import json
import hashlib
from collections import Counter
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textstat
import nltk
from urllib.parse import urlparse


# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


def check_structured_data_richness(html):
    """Analyze richness and variety of structured data for LLM consumption."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all JSON-LD scripts
        jsonld_scripts = soup.find_all('script', type='application/ld+json')
        
        structured_data = {
            'types_found': [],
            'llm_friendly_types': [],
            'total_schemas': 0,
            'richness_score': 0
        }
        
        # LLM-friendly schema types (prioritized for AI understanding)
        llm_priority_types = {
            'Article': 10,
            'NewsArticle': 10,
            'BlogPosting': 9,
            'FAQPage': 10,
            'QAPage': 10,
            'HowTo': 9,
            'Recipe': 8,
            'Product': 8,
            'Service': 7,
            'Organization': 6,
            'Person': 6,
            'Event': 7,
            'Place': 6,
            'Review': 8,
            'VideoObject': 7,
            'ImageObject': 6,
            'Dataset': 9,
            'SoftwareApplication': 7
        }
        
        total_score = 0
        
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string)
                items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                
                for item in items:
                    if isinstance(item, dict) and item.get('@type'):
                        schema_type = item.get('@type')
                        structured_data['types_found'].append(schema_type)
                        structured_data['total_schemas'] += 1
                        
                        if schema_type in llm_priority_types:
                            structured_data['llm_friendly_types'].append(schema_type)
                            total_score += llm_priority_types[schema_type]
                            
                            # Bonus for rich content within schemas
                            if schema_type == 'FAQPage' and item.get('mainEntity'):
                                total_score += 5
                            elif schema_type == 'Article' and item.get('articleBody'):
                                total_score += 3
                            elif schema_type == 'HowTo' and item.get('step'):
                                total_score += 4
                                
            except json.JSONDecodeError:
                continue
        
        # Calculate richness score (0-100)
        max_possible_score = 50  # Reasonable maximum for most sites
        structured_data['richness_score'] = min(100, int((total_score / max_possible_score) * 100))
        
        # Remove duplicates
        structured_data['types_found'] = list(set(structured_data['types_found']))
        structured_data['llm_friendly_types'] = list(set(structured_data['llm_friendly_types']))
        
        if structured_data['llm_friendly_types']:
            return {
                "passed": True,
                "message": f"Found {len(structured_data['llm_friendly_types'])} LLM-friendly schema types",
                "data": structured_data
            }
        else:
            return {
                "passed": False,
                "message": f"Found {structured_data['total_schemas']} schemas but none are LLM-optimized",
                "data": structured_data
            }
            
    except Exception as e:
        return {"passed": False, "message": f"Error analyzing structured data: {str(e)}", "data": {}}


def check_content_readability(html):
    """Analyze content readability using multiple metrics."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract main content (remove nav, footer, sidebar, etc.)
        for element in soup(['nav', 'footer', 'aside', 'header', 'script', 'style']):
            element.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 100:
            return {
                "passed": False,
                "message": "Insufficient content for readability analysis",
                "data": {"word_count": len(text.split())}
            }
        
        # Calculate readability metrics
        flesch_kincaid = textstat.flesch_kincaid_grade(text)
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        gunning_fog = textstat.gunning_fog(text)
        
        # Word and sentence statistics
        word_count = len(text.split())
        sentence_count = textstat.sentence_count(text)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # LLM-friendly readability thresholds
        readability_data = {
            "flesch_kincaid_grade": round(flesch_kincaid, 1),
            "flesch_reading_ease": round(flesch_reading_ease, 1),
            "gunning_fog_index": round(gunning_fog, 1),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "readability_score": 0
        }
        
        # Calculate composite readability score (0-100, higher is better for LLMs)
        score = 0
        
        # Flesch Reading Ease (60-70 is ideal for LLMs)
        if 60 <= flesch_reading_ease <= 70:
            score += 30
        elif 50 <= flesch_reading_ease < 60 or 70 < flesch_reading_ease <= 80:
            score += 25
        elif flesch_reading_ease >= 40:
            score += 15
        
        # Flesch-Kincaid Grade (8-12 is good for LLMs)
        if 8 <= flesch_kincaid <= 12:
            score += 25
        elif 6 <= flesch_kincaid < 8 or 12 < flesch_kincaid <= 15:
            score += 20
        elif flesch_kincaid <= 18:
            score += 10
        
        # Sentence length (15-20 words ideal for LLMs)
        if 15 <= avg_sentence_length <= 20:
            score += 25
        elif 10 <= avg_sentence_length < 15 or 20 < avg_sentence_length <= 25:
            score += 20
        elif avg_sentence_length <= 30:
            score += 10
        
        # Content length bonus
        if word_count >= 300:
            score += 20
        elif word_count >= 150:
            score += 10
        
        readability_data["readability_score"] = min(100, score)
        
        if score >= 70:
            return {
                "passed": True,
                "message": f"Excellent readability for LLMs (score: {readability_data['readability_score']})",
                "data": readability_data
            }
        elif score >= 50:
            return {
                "passed": True,
                "message": f"Good readability for LLMs (score: {readability_data['readability_score']})",
                "data": readability_data
            }
        else:
            return {
                "passed": False,
                "message": f"Poor readability for LLMs (score: {readability_data['readability_score']})",
                "data": readability_data
            }
            
    except Exception as e:
        return {"passed": False, "message": f"Error analyzing readability: {str(e)}", "data": {}}


def extract_llm_readable_content(html, url):
    """Extract and analyze what content LLMs can easily understand."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        content_analysis = {
            "easily_readable": {},
            "challenging": {},
            "inaccessible": {},
            "llm_readiness_score": 0
        }
        
        # EASILY READABLE CONTENT
        # Text content
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        paragraphs = soup.find_all('p')
        lists = soup.find_all(['ul', 'ol'])
        
        content_analysis["easily_readable"] = {
            "headings": len(headings),
            "paragraphs": len(paragraphs),
            "lists": len(lists),
            "text_content_length": len(soup.get_text().strip()),
            "alt_text_images": len([img for img in soup.find_all('img') if img.get('alt')]),
            "structured_data": len(soup.find_all('script', type='application/ld+json'))
        }
        
        # CHALLENGING CONTENT
        tables = soup.find_all('table')
        forms = soup.find_all('form')
        iframes = soup.find_all('iframe')
        
        content_analysis["challenging"] = {
            "tables": len(tables),
            "forms": len(forms),
            "iframes": len(iframes),
            "images_without_alt": len([img for img in soup.find_all('img') if not img.get('alt')])
        }
        
        # INACCESSIBLE CONTENT
        canvas_elements = soup.find_all('canvas')
        svg_without_text = soup.find_all('svg')
        audio_video = soup.find_all(['audio', 'video'])
        
        content_analysis["inaccessible"] = {
            "canvas_elements": len(canvas_elements),
            "svg_elements": len(svg_without_text),
            "media_elements": len(audio_video),
            "javascript_dependent": len(soup.find_all(attrs={"onclick": True}))
        }
        
        # Calculate LLM readiness score
        easily_readable_score = min(50, (
            content_analysis["easily_readable"]["headings"] * 3 +
            content_analysis["easily_readable"]["paragraphs"] * 2 +
            content_analysis["easily_readable"]["lists"] * 2 +
            content_analysis["easily_readable"]["alt_text_images"] * 2 +
            content_analysis["easily_readable"]["structured_data"] * 5
        ))
        
        challenging_penalty = min(20, (
            content_analysis["challenging"]["tables"] * 2 +
            content_analysis["challenging"]["forms"] * 1 +
            content_analysis["challenging"]["images_without_alt"] * 3
        ))
        
        inaccessible_penalty = min(30, (
            content_analysis["inaccessible"]["canvas_elements"] * 5 +
            content_analysis["inaccessible"]["media_elements"] * 3 +
            content_analysis["inaccessible"]["javascript_dependent"] * 2
        ))
        
        content_analysis["llm_readiness_score"] = max(0, easily_readable_score - challenging_penalty - inaccessible_penalty)
        
        if content_analysis["llm_readiness_score"] >= 35:
            return {
                "passed": True,
                "message": f"High LLM content accessibility (score: {content_analysis['llm_readiness_score']})",
                "data": content_analysis
            }
        elif content_analysis["llm_readiness_score"] >= 20:
            return {
                "passed": True,
                "message": f"Moderate LLM content accessibility (score: {content_analysis['llm_readiness_score']})",
                "data": content_analysis
            }
        else:
            return {
                "passed": False,
                "message": f"Low LLM content accessibility (score: {content_analysis['llm_readiness_score']})",
                "data": content_analysis
            }
            
    except Exception as e:
        return {"passed": False, "message": f"Error analyzing LLM content: {str(e)}", "data": {}}


def detect_duplicate_content(pages_data, similarity_threshold=0.8):
    """Detect duplicate or very similar content across pages."""
    try:
        if len(pages_data) < 2:
            return {
                "passed": True,
                "message": "Insufficient pages for duplicate content analysis",
                "data": {"duplicate_groups": [], "similarity_matrix": []}
            }
        
        # Extract text content from each page
        page_texts = []
        page_urls = []
        
        for page in pages_data:
            if page.get('html'):
                soup = BeautifulSoup(page['html'], 'html.parser')
                # Remove navigation, footer, etc.
                for element in soup(['nav', 'footer', 'aside', 'header', 'script', 'style']):
                    element.decompose()
                
                text = soup.get_text()
                text = re.sub(r'\s+', ' ', text).strip()
                
                if len(text) > 100:  # Only analyze pages with substantial content
                    page_texts.append(text)
                    page_urls.append(page['url'])
        
        if len(page_texts) < 2:
            return {
                "passed": True,
                "message": "Insufficient content for duplicate analysis",
                "data": {"duplicate_groups": [], "similarity_matrix": []}
            }
        
        # Calculate TF-IDF similarity
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(page_texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find duplicate groups
        duplicate_groups = []
        processed_indices = set()
        
        for i in range(len(similarity_matrix)):
            if i in processed_indices:
                continue
                
            similar_pages = []
            for j in range(i + 1, len(similarity_matrix)):
                if similarity_matrix[i][j] >= similarity_threshold:
                    if not similar_pages:
                        similar_pages.append({"url": page_urls[i], "index": i})
                    similar_pages.append({"url": page_urls[j], "index": j})
                    processed_indices.add(j)
            
            if similar_pages:
                processed_indices.add(i)
                duplicate_groups.append({
                    "similarity_score": float(max(similarity_matrix[i][j] for j in range(i + 1, len(similarity_matrix)) if similarity_matrix[i][j] >= similarity_threshold)),
                    "pages": similar_pages
                })
        
        # Convert similarity matrix to serializable format
        similarity_data = []
        for i in range(len(similarity_matrix)):
            row = []
            for j in range(len(similarity_matrix[i])):
                row.append(round(float(similarity_matrix[i][j]), 3))
            similarity_data.append(row)
        
        duplicate_data = {
            "duplicate_groups": duplicate_groups,
            "similarity_matrix": similarity_data,
            "page_urls": page_urls,
            "total_duplicates": len(duplicate_groups)
        }
        
        if duplicate_groups:
            return {
                "passed": False,
                "message": f"Found {len(duplicate_groups)} groups of duplicate/similar content",
                "data": duplicate_data
            }
        else:
            return {
                "passed": True,
                "message": "No duplicate content detected",
                "data": duplicate_data
            }
            
    except Exception as e:
        return {"passed": False, "message": f"Error detecting duplicates: {str(e)}", "data": {}}


def generate_llm_recommendations(page_results):
    """Generate specific recommendations for improving LLM readiness."""
    try:
        recommendations = {
            "critical": [],
            "important": [],
            "suggested": [],
            "overall_score": 0
        }
        
        total_score = 0
        total_checks = 0
        
        for page in page_results:
            url = page.get('url', 'Unknown URL')
            checks = page.get('checks', {})
            
            # Analyze each check type
            for check_name, check_result in checks.items():
                total_checks += 1
                if check_result.get('passed'):
                    total_score += 1
                else:
                    # Generate specific recommendations based on failed checks
                    if check_name == 'robots':
                        recommendations["critical"].append(f"Fix robots.txt to allow LLM crawlers on {url}")
                    elif check_name == 'structured_data_richness':
                        recommendations["important"].append(f"Add LLM-friendly structured data (FAQ, Article, HowTo) to {url}")
                    elif check_name == 'content_readability':
                        recommendations["important"].append(f"Improve content readability for LLMs on {url}")
                    elif check_name == 'llm_content_analysis':
                        recommendations["suggested"].append(f"Optimize content structure for LLM understanding on {url}")
                    elif check_name == 'h1':
                        recommendations["important"].append(f"Add clear H1 heading to {url}")
                    elif check_name == 'alt_text':
                        recommendations["suggested"].append(f"Add alt text to all images on {url}")
        
        # Calculate overall score
        if total_checks > 0:
            recommendations["overall_score"] = int((total_score / total_checks) * 100)
        
        # Add general recommendations
        if recommendations["overall_score"] < 70:
            recommendations["critical"].append("Overall LLM readiness is below recommended threshold")
        
        return recommendations
        
    except Exception as e:
        return {
            "critical": [f"Error generating recommendations: {str(e)}"],
            "important": [],
            "suggested": [],
            "overall_score": 0
        }
