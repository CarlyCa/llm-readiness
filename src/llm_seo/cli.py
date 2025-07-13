"""CLI entry point for llm-seo tool."""

import json
import click
import os
from .crawler import crawl_site
from .scoring import calculate_scores
from .openai_reporter import generate_report_with_openai
from .report_generator import generate_unified_report, save_report_to_file


@click.command()
@click.argument('url')
@click.option('--depth', default=1, help='Crawl depth (default: 1)')
@click.option('--output', help='Path to save report file (supports .txt, .md, .json)')
@click.option('--openai-report', is_flag=True, help='Generate polished report using OpenAI (requires OPENAI_API_KEY)')
@click.option('--openai-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
@click.option('--format', type=click.Choice(['report', 'json']), default='report', help='Output format: report (human-readable) or json (raw data)')
def audit(url, depth, output, openai_report, openai_key, format):
    """Audit a website for LLM readiness."""
    click.echo(f"Auditing {url} with depth {depth}...")
    
    # Crawl the site
    pages_data = crawl_site(url, depth)
    
    # Calculate scores
    results = calculate_scores(pages_data)
    
    # Generate OpenAI report if requested
    if openai_report:
        if not openai_key and not os.getenv('OPENAI_API_KEY'):
            click.echo("Error: OpenAI API key required. Set OPENAI_API_KEY environment variable or use --openai-key option.")
            return
        
        click.echo("Generating polished report with OpenAI...")
        
        # Extract HTML data for LLM scraping
        pages_html_data = []
        for page in pages_data:
            if 'html' in page:
                pages_html_data.append({
                    'url': page['url'],
                    'html': page.get('html', '')
                })
        
        openai_result = generate_report_with_openai(results, pages_html_data, openai_key)
        
        if not openai_result['success']:
            click.echo(f"Failed to generate OpenAI report: {openai_result['error']}")
            openai_result = None
    else:
        openai_result = None
    
    # Generate unified report
    if format == 'report':
        unified_report = generate_unified_report(results, openai_result)
        
        if output:
            save_report_to_file(unified_report, output)
            click.echo(f"Report saved to {output}")
        else:
            click.echo(unified_report)
    else:
        # JSON format
        if openai_result and openai_result['success']:
            results['openai_report'] = openai_result['report']
            results['content_analysis'] = openai_result['scraped_content_summary']
        
        if output:
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            click.echo(f"JSON report saved to {output}")
        else:
            click.echo(json.dumps(results, indent=2))


if __name__ == '__main__':
    audit()
