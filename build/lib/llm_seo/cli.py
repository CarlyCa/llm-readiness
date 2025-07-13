"""CLI entry point for llm-seo tool."""

import json
import click
from .crawler import crawl_site
from .scoring import calculate_scores


@click.command()
@click.argument('url')
@click.option('--depth', default=1, help='Crawl depth (default: 1)')
@click.option('--output', help='Path to JSON report file')
def audit(url, depth, output):
    """Audit a website for LLM readiness."""
    click.echo(f"Auditing {url} with depth {depth}...")
    
    # Crawl the site
    pages_data = crawl_site(url, depth)
    
    # Calculate scores
    results = calculate_scores(pages_data)
    
    # Output results
    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(json.dumps(results, indent=2))


if __name__ == '__main__':
    audit()
