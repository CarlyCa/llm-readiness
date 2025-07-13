"""Flask web application for LLM-SEO service."""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import sys
sys.path.append('../llm-seo/src')

# Always load .env from the directory where this file lives
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from llm_seo.crawler import crawl_site
from llm_seo.scoring import calculate_scores
from llm_seo.openai_reporter import generate_report_with_openai
from pdf_generator import generate_pdf_report

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'reports'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create reports directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main page with URL input form."""
    return render_template('index.html')

@app.route('/audit', methods=['POST'])
def audit_website():
    """Process website audit request."""
    try:
        data = request.get_json()
        url = data.get('url')
        depth = int(data.get('depth', 1))
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        
        # Crawl the site
        pages_data = crawl_site(url, depth)
        
        # Calculate scores
        results = calculate_scores(pages_data)
        
        # Always try to generate OpenAI report
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"DEBUG: OpenAI API key found: {'Yes' if api_key else 'No'}")
        print(f"DEBUG: API key length: {len(api_key) if api_key else 0}")
        
        # Extract HTML data for LLM scraping
        pages_html_data = []
        for page in pages_data:
            if 'html' in page:
                pages_html_data.append({
                    'url': page['url'],
                    'html': page.get('html', '')
                })
        
        # Always call OpenAI function - let it handle the key check
        openai_result = generate_report_with_openai(results, pages_html_data)
        print(f"DEBUG: OpenAI result success: {openai_result.get('success', False)}")
        
        if not openai_result.get('success'):
            print(f"DEBUG: OpenAI error: {openai_result.get('error', 'Unknown error')}")
            # Create fallback result
            openai_result = {
                'success': True,
                'report': 'Professional AI analysis requires OpenAI API key configuration. The technical audit above provides comprehensive LLM readiness insights.',
                'scraped_content_summary': {}
            }
        
        # Generate PDF report
        report_filename = f"llm_seo_report_{report_id}.pdf"
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
        generate_pdf_report(results, openai_result, report_path)
        
        # Prepare response data
        response_data = {
            'success': True,
            'report_id': report_id,
            'site_score': results.get('site_score', 0),
            'total_pages': len(results.get('pages', [])),
            'summary': {
                'critical_issues': len(results.get('recommendations', {}).get('critical', [])),
                'important_issues': len(results.get('recommendations', {}).get('important', [])),
                'suggested_improvements': len(results.get('recommendations', {}).get('suggested', [])),
                'accessibility_breakdown': results.get('llm_readiness_summary', {}).get('accessibility_breakdown', {}),
                'content_analysis': results.get('llm_readiness_summary', {}).get('content_analysis', {})
            },
            'has_ai_analysis': openai_result is not None and openai_result.get('success', False),
            'download_url': f'/download/{report_filename}'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"DEBUG: Audit failed with error: {str(e)}")
        return jsonify({'error': f'Audit failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_report(filename):
    """Download report file."""
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True,
            download_name=f"LLM_SEO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    except FileNotFoundError:
        flash('Report file not found.', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
