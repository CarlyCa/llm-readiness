"""Scoring system for LLM-SEO analysis."""

import textstat
from .checks import (
    check_robots_txt_allows_crawling,
    check_meta_robots_allows_indexing,
    check_has_h1_tag,
    check_has_meta_description,
    check_images_have_alt_text
)
from .content_analysis import analyze_content_readability, analyze_structured_data
from .llm_analysis import extract_llm_readable_content
from .llm_scraper import scrape_as_llm, analyze_llm_accessibility
from .openai_scraper import scrape_website_with_openai


def calculate_scores(pages_data):
    """Calculate scores for all pages and generate summary."""
    
    # FIRST: Use OpenAI to analyze what AI can see on the website
    print("🤖 Analyzing website with AI...")
    openai_analysis = scrape_website_with_openai(pages_data)
    
    results = {
        'pages': [],
        'site_score': 0,
        'recommendations': {'critical': [], 'important': [], 'suggested': []},
        'llm_readiness_summary': {
            'accessibility_breakdown': {'high_accessibility': 0, 'medium_accessibility': 0, 'low_accessibility': 0},
            'content_analysis': {'avg_readability_score': 0, 'avg_structured_data_richness': 0, 'total_structured_schemas': 0}
        },
        'openai_analysis': openai_analysis  # Include AI analysis in results
    }
    
    total_score = 0
    total_readability = 0
    total_structured_data = 0
    total_schemas = 0
    
    for page_data in pages_data:
        page_result = score_page(page_data)
        results['pages'].append(page_result)
        total_score += page_result['score']
        
        # Aggregate content analysis
        content_analysis = page_result.get('content_analysis', {})
        total_readability += content_analysis.get('readability_score', 0)
        total_structured_data += content_analysis.get('structured_data_richness', 0)
        total_schemas += content_analysis.get('structured_schemas_count', 0)
        
        # Categorize accessibility
        score = page_result['score']
        if score >= 80:
            results['llm_readiness_summary']['accessibility_breakdown']['high_accessibility'] += 1
        elif score >= 50:
            results['llm_readiness_summary']['accessibility_breakdown']['medium_accessibility'] += 1
        else:
            results['llm_readiness_summary']['accessibility_breakdown']['low_accessibility'] += 1
    
    # Calculate averages
    num_pages = len(pages_data)
    if num_pages > 0:
        results['site_score'] = round(total_score / num_pages)
        results['llm_readiness_summary']['content_analysis']['avg_readability_score'] = round(total_readability / num_pages)
        results['llm_readiness_summary']['content_analysis']['avg_structured_data_richness'] = round(total_structured_data / num_pages)
        results['llm_readiness_summary']['content_analysis']['total_structured_schemas'] = total_schemas
    
    # Generate website-specific recommendations using AI insights
    if openai_analysis.get('success'):
        results['recommendations'] = generate_ai_powered_recommendations(results, openai_analysis)
    else:
        results['recommendations'] = generate_recommendations(results)
    
    return results


def score_page(page_data):
    """Score a single page."""
    
    # FIRST: Analyze what AI can see on this page
    llm_content = scrape_as_llm(page_data['html'], page_data['url'])
    llm_accessibility = analyze_llm_accessibility(page_data['html'], page_data['url'])
    llm_readable_content = extract_llm_readable_content(page_data['html'], page_data['url'])
    
    checks = {
        # AI Content Analysis (what LLMs can actually see)
        'llm_content_analysis': llm_readable_content,
        'llm_accessibility_analysis': {
            'passed': True,
            'message': f"LLM can access {len(llm_content.get('headings', []))} headings, {len(llm_content.get('main_content', '').split())} words of content",
            'data': llm_accessibility
        },
        'llm_content_richness': {
            'passed': llm_content.get('llm_richness_score', 0) >= 50,
            'message': f"Content richness score: {llm_content.get('llm_richness_score', 0)}/100",
            'data': llm_content
        },
        
        # Traditional technical checks
        'robots_txt_allows_crawling': check_robots_txt_allows_crawling(page_data),
        'meta_robots_allows_indexing': check_meta_robots_allows_indexing(page_data),
        'has_h1_tag': check_has_h1_tag(page_data),
        'has_meta_description': check_has_meta_description(page_data),
        'images_have_alt_text': check_images_have_alt_text(page_data)
    }
    
    # Content analysis
    content_analysis = {
        'readability_score': analyze_content_readability(page_data),
        'structured_data_richness': analyze_structured_data(page_data)['richness_score'],
        'structured_schemas_count': analyze_structured_data(page_data)['schema_count'],
        'llm_content_summary': {
            'title': llm_content.get('title', ''),
            'headings_count': len(llm_content.get('headings', [])),
            'main_content_words': len(llm_content.get('main_content', '').split()),
            'images_with_alt': len(llm_content.get('images_with_context', [])),
            'structured_schemas': len(llm_content.get('structured_data', [])),
            'richness_score': llm_content.get('llm_richness_score', 0)
        }
    }
    
    # Calculate score (each check worth 20 points, but prioritize LLM checks)
    score = 0
    for check_name, check_result in checks.items():
        if check_result['passed']:
            # Give extra weight to LLM-specific checks
            if check_name.startswith('llm_'):
                score += 25
            else:
                score += 15
    
    # Cap at 100
    score = min(100, score)
    
    return {
        'url': page_data['url'],
        'score': score,
        'checks': checks,
        'content_analysis': content_analysis
    }


def generate_ai_powered_recommendations(results, openai_analysis):
    """Generate website-specific recommendations using AI insights."""
    
    recommendations = {'critical': [], 'important': [], 'suggested': []}
    
    # Use AI-generated website-specific recommendations
    ai_recommendations = openai_analysis.get('website_specific_recommendations', [])
    
    # Categorize AI recommendations
    for i, rec in enumerate(ai_recommendations):
        if i < 3:  # First 3 are critical
            recommendations['critical'].append(f"🤖 AI INSIGHT: {rec}")
        elif i < 6:  # Next 3 are important
            recommendations['important'].append(f"🤖 AI INSIGHT: {rec}")
        else:  # Rest are suggested
            recommendations['suggested'].append(f"🤖 AI INSIGHT: {rec}")
    
    # Add technical issues with website-specific context
    total_pages = len(results['pages'])
    domain = openai_analysis.get('content_summary', {}).get('domain', 'your website')
    
    # Critical issues with website context
    robots_issues = sum(1 for page in results['pages'] if not page['checks']['robots_txt_allows_crawling']['passed'])
    if robots_issues > 0:
        recommendations['critical'].append(f"🚨 URGENT: {robots_issues} pages on {domain} are blocked by robots.txt - AI assistants can't access these pages at all. Check {domain}/robots.txt and remove 'Disallow: /' rules.")
    
    h1_issues = sum(1 for page in results['pages'] if not page['checks']['has_h1_tag']['passed'])
    if h1_issues > total_pages * 0.5:
        # Get actual page titles from AI analysis for specific examples
        sample_pages = openai_analysis.get('content_summary', {}).get('pages', [])
        example_page = sample_pages[0]['url'] if sample_pages else f"{domain}/page"
        recommendations['critical'].append(f"🚨 URGENT: {h1_issues} pages on {domain} are missing main headings - AI doesn't know what these pages are about. For example, add an H1 heading to {example_page}.")
    
    # Important issues with website context
    meta_desc_issues = sum(1 for page in results['pages'] if not page['checks']['has_meta_description']['passed'])
    if meta_desc_issues > 0:
        business_context = "your business" 
        if sample_pages and sample_pages[0].get('main_content'):
            content = sample_pages[0]['main_content'][:100].lower()
            if 'psychology' in content or 'therapy' in content:
                business_context = "psychology services"
            elif 'restaurant' in content or 'food' in content:
                business_context = "restaurant"
            elif 'shop' in content or 'store' in content:
                business_context = "store"
        
        recommendations['important'].append(f"⚠️ Add page descriptions to {meta_desc_issues} pages on {domain} - write 1-2 sentences explaining what visitors will find. Example for {business_context}: 'Professional [service] available in [location]. [Key benefit or specialization].'")
    
    alt_text_issues = sum(1 for page in results['pages'] if not page['checks']['images_have_alt_text']['passed'])
    if alt_text_issues > 0:
        recommendations['important'].append(f"⚠️ Add descriptions to images on {alt_text_issues} pages of {domain} - AI can't see pictures, only text descriptions. Describe what's actually in your images related to your business.")
    
    return recommendations

def generate_recommendations(results):
    """Generate recommendations based on analysis."""
    
    recommendations = {'critical': [], 'important': [], 'suggested': []}
    
    # Analyze common issues
    total_pages = len(results['pages'])
    
    # Critical issues - with actionable instructions
    robots_issues = sum(1 for page in results['pages'] if not page['checks']['robots_txt_allows_crawling']['passed'])
    if robots_issues > 0:
        recommendations['critical'].append(f"URGENT: Fix robots.txt blocking on {robots_issues} pages - AI assistants can't access these pages at all. Check yourwebsite.com/robots.txt and remove 'Disallow: /' rules.")
    
    meta_robots_issues = sum(1 for page in results['pages'] if not page['checks']['meta_robots_allows_indexing']['passed'])
    if meta_robots_issues > 0:
        recommendations['critical'].append(f"URGENT: Remove 'noindex' tags from {meta_robots_issues} pages - these tags tell AI 'don't read this page.' Ask your developer to remove <meta name='robots' content='noindex'> from pages you want AI to see.")
    
    h1_issues = sum(1 for page in results['pages'] if not page['checks']['has_h1_tag']['passed'])
    if h1_issues > total_pages * 0.5:
        recommendations['critical'].append(f"URGENT: Add clear main headings to {h1_issues} pages - AI needs these to understand what each page is about. Add an H1 heading like 'Emergency Plumbing Services in Chicago' instead of just 'Services.'")
    
    # Important issues - with specific instructions
    meta_desc_issues = sum(1 for page in results['pages'] if not page['checks']['has_meta_description']['passed'])
    if meta_desc_issues > 0:
        recommendations['important'].append(f"Add page descriptions to {meta_desc_issues} pages - write 1-2 sentences (120-160 characters) explaining what visitors will find on each page. Example: 'Professional emergency plumbing services available 24/7 in Chicago. Licensed plumbers for repairs, installations, and maintenance.'")
    
    alt_text_issues = sum(1 for page in results['pages'] if not page['checks']['images_have_alt_text']['passed'])
    if alt_text_issues > 0:
        recommendations['important'].append(f"Add descriptions to images on {alt_text_issues} pages - AI can't see pictures, only text descriptions. Add alt text like 'Team photo of ABC Company staff in office' or 'Red leather sofa with chrome legs, model XYZ-123.'")
    
    # Suggested improvements - with clear benefits
    if results['llm_readiness_summary']['content_analysis']['avg_readability_score'] < 70:
        recommendations['suggested'].append("Simplify your writing for better AI understanding - use shorter sentences (15-20 words), replace jargon with simple terms, and add more headings. This helps AI explain your content more accurately to users.")
    
    if results['llm_readiness_summary']['content_analysis']['total_structured_schemas'] == 0:
        recommendations['suggested'].append("Add content labels (structured data) to help AI understand what type of content you have - mark articles as 'Article,' products as 'Product,' and FAQs as 'FAQPage.' This helps AI give more relevant answers when people ask questions about your industry.")
    
    return recommendations
