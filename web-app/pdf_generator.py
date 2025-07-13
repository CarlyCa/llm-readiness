"""Professional PDF report generator for LLM-SEO analysis."""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, String, Rect, Line, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from urllib.parse import urlparse
import math


class ProfessionalLLMSEOPDFReport:
    """Generate professional PDF reports for LLM-SEO analysis."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_professional_styles()
        
    def setup_professional_styles(self):
        """Setup professional styles for the PDF."""
        # Modern color palette
        self.colors = {
            'primary': HexColor('#1e40af'),      # Deep blue
            'secondary': HexColor('#3b82f6'),    # Blue
            'success': HexColor('#059669'),      # Green
            'warning': HexColor('#d97706'),      # Orange
            'danger': HexColor('#dc2626'),       # Red
            'dark': HexColor('#1f2937'),         # Dark gray
            'light': HexColor('#f3f4f6'),        # Light gray
            'white': white,
            'black': black
        }
        
        # Professional title style
        self.styles.add(ParagraphStyle(
            name='ProfessionalTitle',
            parent=self.styles['Title'],
            fontSize=28,
            spaceAfter=30,
            textColor=self.colors['primary'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceBefore=20
        ))
        
        # Section heading with accent line
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            spaceBefore=25,
            textColor=self.colors['dark'],
            fontName='Helvetica-Bold',
            leftIndent=0
        ))
        
        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=self.colors['primary'],
            fontName='Helvetica-Bold'
        ))
        
        # Score display style
        self.styles.add(ParagraphStyle(
            name='ScoreDisplay',
            parent=self.styles['Normal'],
            fontSize=48,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=10,
            spaceBefore=10
        ))
        
        # Metric style
        self.styles.add(ParagraphStyle(
            name='MetricStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            leftIndent=20,
            fontName='Helvetica'
        ))
        
        # Issue styles with icons
        self.styles.add(ParagraphStyle(
            name='CriticalIssue',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25,
            textColor=self.colors['danger'],
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ImportantIssue',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25,
            textColor=self.colors['warning'],
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SuggestedIssue',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25,
            textColor=self.colors['secondary'],
            fontName='Helvetica'
        ))
        
        # Executive summary style
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leftIndent=0,
            rightIndent=0
        ))
        
        # Callout box style
        self.styles.add(ParagraphStyle(
            name='CalloutBox',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=15,
            rightIndent=15,
            fontName='Helvetica',
            backColor=self.colors['light']
        ))

    def create_header_footer(self, doc):
        """Create professional header and footer."""
        def header_footer(canvas, doc):
            canvas.saveState()
            
            # Header
            canvas.setFillColor(self.colors['primary'])
            canvas.rect(0, doc.height + doc.topMargin - 0.5*inch, doc.width + doc.leftMargin + doc.rightMargin, 0.5*inch, fill=1)
            
            canvas.setFillColor(self.colors['white'])
            canvas.setFont('Helvetica-Bold', 14)
            canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.3*inch, "LLM-SEO AUDIT REPORT")
            
            # Footer
            canvas.setFillColor(self.colors['light'])
            canvas.rect(0, 0, doc.width + doc.leftMargin + doc.rightMargin, 0.3*inch, fill=1)
            
            canvas.setFillColor(self.colors['dark'])
            canvas.setFont('Helvetica', 9)
            canvas.drawString(doc.leftMargin, 0.15*inch, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            canvas.drawRightString(doc.width + doc.leftMargin, 0.15*inch, "Page " + str(doc.page))
            
            canvas.restoreState()
        
        return header_footer

    def create_score_chart(self, score):
        """Create a circular progress chart for the score."""
        drawing = Drawing(200, 200)
        
        # Background circle
        drawing.add(Circle(100, 100, 80, fillColor=self.colors['light'], strokeColor=self.colors['dark'], strokeWidth=2))
        
        # Progress arc
        angle = (score / 100) * 360
        if angle > 0:
            drawing.add(Circle(100, 100, 80, fillColor=None, strokeColor=self.get_score_color(score), strokeWidth=8))
        
        # Score text
        drawing.add(String(100, 95, f"{score}", fontSize=24, fillColor=self.get_score_color(score), textAnchor='middle', fontName='Helvetica-Bold'))
        drawing.add(String(100, 75, "/100", fontSize=12, fillColor=self.colors['dark'], textAnchor='middle', fontName='Helvetica'))
        
        return drawing

    def create_issues_pie_chart(self, recommendations):
        """Create a pie chart showing issue distribution."""
        drawing = Drawing(300, 200)
        
        pie = Pie()
        pie.x = 150
        pie.y = 100
        pie.width = 120
        pie.height = 120
        
        critical = len(recommendations.get('critical', []))
        important = len(recommendations.get('important', []))
        suggested = len(recommendations.get('suggested', []))
        
        if critical + important + suggested > 0:
            pie.data = [critical, important, suggested]
            pie.labels = ['Critical', 'Important', 'Suggested']
            pie.slices.strokeWidth = 2
            pie.slices.strokeColor = self.colors['white']
            pie.slices[0].fillColor = self.colors['danger']
            pie.slices[1].fillColor = self.colors['warning']
            pie.slices[2].fillColor = self.colors['secondary']
            
            drawing.add(pie)
        
        return drawing

    def create_accessibility_bar_chart(self, accessibility_breakdown):
        """Create a bar chart showing accessibility distribution."""
        drawing = Drawing(400, 200)
        
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.width = 300
        chart.height = 120
        
        high = accessibility_breakdown.get('high_accessibility', 0)
        medium = accessibility_breakdown.get('medium_accessibility', 0)
        low = accessibility_breakdown.get('low_accessibility', 0)
        
        chart.data = [[high, medium, low]]
        chart.categoryAxis.categoryNames = ['High', 'Medium', 'Low']
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(high, medium, low, 1)
        chart.valueAxis.valueStep = 1
        
        chart.bars[0].fillColor = self.colors['success']
        chart.bars[1].fillColor = self.colors['warning']
        chart.bars[2].fillColor = self.colors['danger']
        
        drawing.add(chart)
        
        return drawing

    def generate_pdf_report(self, audit_results, openai_result, filename):
        """Generate a professional PDF report."""
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=80,
            bottomMargin=50
        )
        
        # Add header and footer
        doc.build = lambda story: SimpleDocTemplate.build(doc, story, onFirstPage=self.create_header_footer(doc), onLaterPages=self.create_header_footer(doc))
        
        story = []
        
        # Cover page
        story.append(Paragraph("LLM-SEO READINESS AUDIT", self.styles['ProfessionalTitle']))
        story.append(Spacer(1, 40))
        
        # Report metadata in a professional table
        site_url = audit_results.get('pages', [{}])[0].get('url', 'Unknown')
        domain = urlparse(site_url).netloc if site_url != 'Unknown' else 'Unknown'
        
        metadata_data = [
            ['Website Analyzed:', domain],
            ['Analysis Date:', datetime.now().strftime('%B %d, %Y')],
            ['Pages Crawled:', str(len(audit_results.get('pages', [])))],
            ['Analysis Type:', 'AI-Powered LLM Readiness Audit'],
            ['Report Version:', 'Professional v2.0']
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2.5*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light']),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['primary']),
        ]))
        
        story.append(metadata_table)
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeading']))
        
        # Overall Score with chart
        site_score = audit_results.get('site_score', 0)
        score_chart = self.create_score_chart(site_score)
        story.append(score_chart)
        
        score_style = ParagraphStyle(
            name='DynamicScore',
            parent=self.styles['ScoreDisplay'],
            textColor=self.get_score_color(site_score)
        )
        story.append(Paragraph(f"{site_score}/100", score_style))
        story.append(Paragraph(self.get_score_description(site_score), self.styles['ExecutiveSummary']))
        story.append(Spacer(1, 20))
        
        # Key metrics in a professional grid
        recommendations = audit_results.get('recommendations', {})
        llm_summary = audit_results.get('llm_readiness_summary', {})
        
        metrics_data = [
            ['Critical Issues', f"{len(recommendations.get('critical', []))}", 'Immediate attention required'],
            ['Important Issues', f"{len(recommendations.get('important', []))}", 'Should be addressed soon'],
            ['Suggested Improvements', f"{len(recommendations.get('suggested', []))}", 'Enhancement opportunities'],
            ['High Accessibility Pages', f"{llm_summary.get('accessibility_breakdown', {}).get('high_accessibility', 0)}", 'Well-optimized for AI'],
            ['Medium Accessibility Pages', f"{llm_summary.get('accessibility_breakdown', {}).get('medium_accessibility', 0)}", 'Some optimization needed'],
            ['Low Accessibility Pages', f"{llm_summary.get('accessibility_breakdown', {}).get('low_accessibility', 0)}", 'Requires significant work']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light']),
            ('BACKGROUND', (1, 0), (1, -1), self.colors['white']),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors['primary']),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 25))
        
        # Visual charts
        story.append(Paragraph("ISSUE DISTRIBUTION", self.styles['SubHeading']))
        issues_chart = self.create_issues_pie_chart(recommendations)
        story.append(issues_chart)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("ACCESSIBILITY BREAKDOWN", self.styles['SubHeading']))
        accessibility_chart = self.create_accessibility_bar_chart(llm_summary.get('accessibility_breakdown', {}))
        story.append(accessibility_chart)
        story.append(PageBreak())
        
        # AI Analysis Section
        if openai_result and openai_result.get('success'):
            story.append(Paragraph("AI-POWERED ANALYSIS & RECOMMENDATIONS", self.styles['SectionHeading']))
            
            # Create a callout box for AI insights
            ai_report = openai_result.get('report', '')
            paragraphs = ai_report.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    if para.strip().startswith('##') or para.strip().startswith('**') or para.strip().isupper():
                        story.append(Paragraph(para.strip().replace('##', '').replace('**', ''), self.styles['SubHeading']))
                    else:
                        story.append(Paragraph(para.strip(), self.styles['ExecutiveSummary']))
                    story.append(Spacer(1, 8))
        
        # Detailed Recommendations with icons
        if recommendations.get('critical'):
            story.append(PageBreak())
            story.append(Paragraph("🚨 CRITICAL ISSUES (Fix Immediately)", self.styles['SectionHeading']))
            for rec in recommendations['critical']:
                story.append(Paragraph(f"• {rec}", self.styles['CriticalIssue']))
            story.append(Spacer(1, 15))
        
        if recommendations.get('important'):
            story.append(Paragraph("⚠️ IMPORTANT IMPROVEMENTS", self.styles['SectionHeading']))
            for rec in recommendations['important']:
                story.append(Paragraph(f"• {rec}", self.styles['ImportantIssue']))
            story.append(Spacer(1, 15))
        
        if recommendations.get('suggested'):
            story.append(Paragraph("💡 SUGGESTED ENHANCEMENTS", self.styles['SectionHeading']))
            for rec in recommendations['suggested']:
                story.append(Paragraph(f"• {rec}", self.styles['SuggestedIssue']))
            story.append(Spacer(1, 15))
        
        # Page-by-Page Analysis with better formatting
        story.append(PageBreak())
        story.append(Paragraph("📄 PAGE-BY-PAGE ANALYSIS", self.styles['SectionHeading']))
        
        for i, page in enumerate(audit_results.get('pages', [])):
            url = page.get('url', 'Unknown URL')
            score = page.get('score', 0)
            checks = page.get('checks', {})
            
            # Page header with score
            page_header = f"Page {i+1}: {url}"
            story.append(Paragraph(page_header, self.styles['SubHeading']))
            
            # Score indicator
            score_color = self.get_score_color(score)
            story.append(Paragraph(f"Score: <font color='{score_color}'>{score}/100</font>", self.styles['MetricStyle']))
            
            # Show failed checks in a table
            failed_checks = []
            for check_name, check_result in checks.items():
                if not check_result.get('passed', False):
                    failed_checks.append([check_name, check_result.get('message', 'Failed')])
            
            if failed_checks:
                story.append(Paragraph("Issues Found:", self.styles['Normal']))
                issues_table = Table(failed_checks, colWidths=[2*inch, 4*inch])
                issues_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 0), (0, -1), self.colors['light']),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.colors['dark']),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(issues_table)
            else:
                story.append(Paragraph("✅ All checks passed", self.styles['MetricStyle']))
            
            story.append(Spacer(1, 20))
        
        # Professional footer
        story.append(PageBreak())
        story.append(Spacer(1, 100))
        
        footer_data = [
            ['Report generated by LLM-SEO Professional Analyzer'],
            ['Powered by advanced AI analysis and machine learning'],
            ['For technical support or questions, contact your development team']
        ]
        
        footer_table = Table(footer_data, colWidths=[6*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['dark']),
        ]))
        
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        return filename
    
    def get_score_color(self, score):
        """Get color based on score."""
        if score >= 80:
            return '#059669'  # Green
        elif score >= 60:
            return '#2563eb'  # Blue
        elif score >= 40:
            return '#d97706'  # Orange
        else:
            return '#dc2626'  # Red
    
    def get_score_description(self, score):
        """Get description based on score."""
        if score >= 80:
            return "Excellent LLM readiness. Your website is well-optimized for AI crawlers and demonstrates strong compatibility with modern language models."
        elif score >= 60:
            return "Good LLM readiness. Your website shows solid AI compatibility with some opportunities for optimization to maximize AI visibility and understanding."
        elif score >= 40:
            return "Fair LLM readiness. Several areas require attention to improve AI accessibility and content understanding by language models."
        else:
            return "Poor LLM readiness. Significant improvements are needed to make your content accessible and understandable by AI systems and crawlers."


def generate_pdf_report(audit_results, openai_result, filename):
    """Generate a professional PDF report."""
    generator = ProfessionalLLMSEOPDFReport()
    return generator.generate_pdf_report(audit_results, openai_result, filename)
