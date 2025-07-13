"""Scoring system for LLM readiness audit."""


def calculate_scores(pages_data):
    """Calculate overall site score from individual page results."""
    if not pages_data:
        return {
            "pages": [],
            "site_score": 0
        }
    
    total_score = sum(page['score'] for page in pages_data)
    site_score = int(total_score / len(pages_data))
    
    return {
        "pages": pages_data,
        "site_score": site_score
    }
