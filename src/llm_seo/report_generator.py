"""Unified report generator that combines technical metrics with OpenAI analysis."""

import json
from datetime import datetime


def generate_unified_report(audit_results, openai_result=None):
    """Generate a comprehensive report combining technical metrics and AI analysis."""
    
    # Extract key metrics
    site_score = audit_results.get('site_score', 0)
    total_pages = len(audit_results.get('pages', []))
    recommendations = audit_results.get('recommendations', {})
    llm_summary = audit_results.get('llm_readiness_summary', {})
    duplicate_analysis = audit_results.get('duplicate_content_analysis', {})
    
    # Start building the report
    report_lines = []
    
    # Header
    report_lines.extend([
        "=" * 80,
        "LLM READINESS AUDIT REPORT",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Pages Analyzed: {total_pages}",
        f"Overall Score: {site_score}/100",
        "",
    ])
    
    # FIRST: Show what AI can actually see on the website
    report_lines.extend([
        "🤖 WHAT AI CAN SEE ON YOUR WEBSITE",
        "=" * 80,
        "",
        "This analysis shows exactly what Large Language Models and AI systems",
        "can access and understand when they visit your website pages.",
        "",
    ])
    
    # Aggregate LLM-visible content across all pages
    total_accessible = {"headings": 0, "paragraphs": 0, "lists": 0, "images_with_alt": 0, "structured_data": 0}
    total_challenging = {"tables": 0, "forms": 0, "iframes": 0, "images_without_alt": 0}
    total_inaccessible = {"canvas": 0, "svg": 0, "media": 0, "js_dependent": 0}
    total_content_words = 0
    total_richness_score = 0
    pages_with_content = 0
    
    for page in audit_results.get('pages', []):
        # Get LLM content analysis
        llm_analysis = page.get('checks', {}).get('llm_content_analysis', {}).get('data', {})
        content_summary = page.get('content_analysis', {}).get('llm_content_summary', {})
        
        if content_summary:
            total_content_words += content_summary.get('main_content_words', 0)
            total_richness_score += content_summary.get('richness_score', 0)
            pages_with_content += 1
        
        if llm_analysis:
            easily_readable = llm_analysis.get('easily_readable', {})
            challenging = llm_analysis.get('challenging', {})
            inaccessible = llm_analysis.get('inaccessible', {})
            
            total_accessible["headings"] += easily_readable.get('headings', 0)
            total_accessible["paragraphs"] += easily_readable.get('paragraphs', 0)
            total_accessible["lists"] += easily_readable.get('lists', 0)
            total_accessible["images_with_alt"] += easily_readable.get('alt_text_images', 0)
            total_accessible["structured_data"] += easily_readable.get('structured_data', 0)
            
            total_challenging["tables"] += challenging.get('tables', 0)
            total_challenging["forms"] += challenging.get('forms', 0)
            total_challenging["iframes"] += challenging.get('iframes', 0)
            total_challenging["images_without_alt"] += challenging.get('images_without_alt', 0)
            
            total_inaccessible["canvas"] += inaccessible.get('canvas_elements', 0)
            total_inaccessible["svg"] += inaccessible.get('svg_elements', 0)
            total_inaccessible["media"] += inaccessible.get('media_elements', 0)
            total_inaccessible["js_dependent"] += inaccessible.get('javascript_dependent', 0)
    
    avg_richness = total_richness_score / pages_with_content if pages_with_content > 0 else 0
    
    report_lines.extend([
        "✅ CONTENT AI CAN EASILY ACCESS:",
        "-" * 50,
        f"• Text Content: {total_content_words:,} words across all pages",
        f"• Headings (H1-H6): {total_accessible['headings']} total",
        f"• Paragraphs: {total_accessible['paragraphs']} total",
        f"• Lists: {total_accessible['lists']} total", 
        f"• Images with descriptions: {total_accessible['images_with_alt']} total",
        f"• Structured data schemas: {total_accessible['structured_data']} total",
        f"• Average content richness: {avg_richness:.1f}/100",
        "",
        "⚠️ CONTENT CHALLENGING FOR AI:",
        "-" * 50,
        f"• Tables: {total_challenging['tables']} (complex structure to parse)",
        f"• Forms: {total_challenging['forms']} (interactive elements AI can't use)",
        f"• Embedded content: {total_challenging['iframes']} iFrames",
        f"• Images without descriptions: {total_challenging['images_without_alt']}",
        "",
        "❌ CONTENT AI CANNOT ACCESS:",
        "-" * 50,
        f"• Visual graphics: {total_inaccessible['canvas']} canvas + {total_inaccessible['svg']} SVG elements",
        f"• Audio/Video: {total_inaccessible['media']} multimedia elements",
        f"• JavaScript-dependent: {total_inaccessible['js_dependent']} dynamic elements",
        "",
        "💡 WHAT THIS MEANS:",
        "-" * 50,
        "• EASILY ACCESSIBLE: AI can read, understand, and reference this content",
        "• CHALLENGING: AI can access but may misinterpret structure or context", 
        "• CANNOT ACCESS: AI has no way to process this content at all",
        "",
        "=" * 80,
        "",
    ])
    
    # Executive Summary
    report_lines.extend([
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"• Site Score: {site_score}/100",
        f"• Critical Issues: {len(recommendations.get('critical', []))}",
        f"• Important Issues: {len(recommendations.get('important', []))}",
        f"• Suggested Improvements: {len(recommendations.get('suggested', []))}",
        "",
    ])
    
    # LLM Accessibility Breakdown
    accessibility = llm_summary.get('accessibility_breakdown', {})
    report_lines.extend([
        "LLM ACCESSIBILITY BREAKDOWN",
        "-" * 40,
        f"• High Accessibility Pages: {accessibility.get('high_accessibility', 0)}",
        f"• Medium Accessibility Pages: {accessibility.get('medium_accessibility', 0)}",
        f"• Low Accessibility Pages: {accessibility.get('low_accessibility', 0)}",
        "",
    ])
    
    # Content Analysis
    content_analysis = llm_summary.get('content_analysis', {})
    report_lines.extend([
        "CONTENT ANALYSIS",
        "-" * 40,
        f"• Average Readability Score: {content_analysis.get('avg_readability_score', 0)}/100",
        f"• Average Structured Data Richness: {content_analysis.get('avg_structured_data_richness', 0)}/100",
        f"• Total Structured Schemas: {content_analysis.get('total_structured_schemas', 0)}",
        f"• Pages with Good Readability: {content_analysis.get('pages_with_good_readability', 0)}",
        "",
    ])
    
    # Technical Issues Summary
    technical_issues = llm_summary.get('technical_issues', {})
    report_lines.extend([
        "TECHNICAL ISSUES SUMMARY",
        "-" * 40,
        f"• Robots Blocked: {technical_issues.get('robots_blocked', 0)} pages",
        f"• Missing H1 Tags: {technical_issues.get('missing_h1', 0)} pages",
        f"• Missing Alt Text: {technical_issues.get('missing_alt_text', 0)} pages",
        f"• No Structured Data: {technical_issues.get('no_structured_data', 0)} pages",
        "",
    ])
    
    # Duplicate Content Analysis
    if duplicate_analysis.get('data', {}).get('total_duplicates', 0) > 0:
        report_lines.extend([
            "DUPLICATE CONTENT ISSUES",
            "-" * 40,
            f"• {duplicate_analysis['data']['total_duplicates']} groups of duplicate/similar content found",
            f"• {duplicate_analysis.get('message', '')}",
            "",
        ])
    
    # Page-by-Page Analysis
    report_lines.extend([
        "PAGE-BY-PAGE ANALYSIS",
        "-" * 40,
    ])
    
    for page in audit_results.get('pages', []):
        url = page.get('url', 'Unknown URL')
        score = page.get('score', 0)
        checks = page.get('checks', {})
        
        report_lines.append(f"PAGE: {url}")
        report_lines.append(f"   Score: {score}/100")
        
        # Add detailed LLM visibility analysis
        llm_analysis = checks.get('llm_content_analysis', {}).get('data', {})
        if llm_analysis:
            report_lines.extend([
                "   LLM CONTENT VISIBILITY:",
                f"     EASILY ACCESSIBLE:",
                f"       - Headings: {llm_analysis.get('easily_readable', {}).get('headings', 0)}",
                f"       - Paragraphs: {llm_analysis.get('easily_readable', {}).get('paragraphs', 0)}",
                f"       - Lists: {llm_analysis.get('easily_readable', {}).get('lists', 0)}",
                f"       - Images with alt text: {llm_analysis.get('easily_readable', {}).get('alt_text_images', 0)}",
                f"       - Structured data schemas: {llm_analysis.get('easily_readable', {}).get('structured_data', 0)}",
                f"       - Text content length: {llm_analysis.get('easily_readable', {}).get('text_content_length', 0)} characters",
                f"     CHALLENGING FOR LLMs:",
                f"       - Tables: {llm_analysis.get('challenging', {}).get('tables', 0)}",
                f"       - Forms: {llm_analysis.get('challenging', {}).get('forms', 0)}",
                f"       - iFrames: {llm_analysis.get('challenging', {}).get('iframes', 0)}",
                f"       - Images without alt text: {llm_analysis.get('challenging', {}).get('images_without_alt', 0)}",
                f"     INACCESSIBLE TO LLMs:",
                f"       - Canvas elements: {llm_analysis.get('inaccessible', {}).get('canvas_elements', 0)}",
                f"       - SVG elements: {llm_analysis.get('inaccessible', {}).get('svg_elements', 0)}",
                f"       - Audio/Video elements: {llm_analysis.get('inaccessible', {}).get('media_elements', 0)}",
                f"       - JavaScript-dependent content: {llm_analysis.get('inaccessible', {}).get('javascript_dependent', 0)}",
            ])
        
        # Show failed checks
        failed_checks = []
        for check_name, check_result in checks.items():
            if not check_result.get('passed', False):
                failed_checks.append(f"{check_name}: {check_result.get('message', 'Failed')}")
        
        if failed_checks:
            report_lines.append("   ISSUES:")
            for issue in failed_checks:
                report_lines.append(f"   - {issue}")
        else:
            report_lines.append("   STATUS: All checks passed")
        
        report_lines.append("")
    
    # Recommendations
    if recommendations.get('critical'):
        report_lines.extend([
            "CRITICAL ISSUES (Fix Immediately)",
            "-" * 40,
        ])
        for rec in recommendations['critical']:
            report_lines.append(f"- {rec}")
        report_lines.append("")
    
    if recommendations.get('important'):
        report_lines.extend([
            "IMPORTANT IMPROVEMENTS",
            "-" * 40,
        ])
        for rec in recommendations['important']:
            report_lines.append(f"- {rec}")
        report_lines.append("")
    
    if recommendations.get('suggested'):
        report_lines.extend([
            "SUGGESTED ENHANCEMENTS",
            "-" * 40,
        ])
        for rec in recommendations['suggested']:
            report_lines.append(f"- {rec}")
        report_lines.append("")
    
    # OpenAI Analysis (if available)
    if openai_result and openai_result.get('success'):
        report_lines.extend([
            "=" * 80,
            "AI-POWERED ANALYSIS & RECOMMENDATIONS",
            "=" * 80,
            "",
            openai_result['report'],
            "",
        ])
        
        # Content Summary from LLM Scraping
        content_summary = openai_result.get('scraped_content_summary', {})
        if content_summary:
            report_lines.extend([
                "LLM CONTENT SCRAPING SUMMARY",
                "-" * 40,
                f"- Pages Successfully Scraped: {content_summary.get('total_pages_scraped', 0)}",
                f"- Pages with Errors: {content_summary.get('pages_with_errors', 0)}",
                f"- Average Content Richness: {content_summary.get('average_content_richness', 0)}/100",
                f"- Total Structured Schemas Found: {content_summary.get('total_structured_schemas', 0)}",
                f"- Images with Alt Text: {content_summary.get('total_images_with_alt', 0)}",
                f"- Pages with Good Heading Structure: {content_summary.get('pages_with_good_headings', 0)}",
                "",
            ])
    
    # Footer
    report_lines.extend([
        "=" * 80,
        "End of Report",
        "=" * 80,
    ])
    
    return "\n".join(report_lines)


def save_report_to_file(report_content, filename):
    """Save the unified report to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
