"""
PDF report generator for creating downloadable reports.
Includes dataset overview, statistics, visualizations, and insights.
"""

import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image as PILImage
import plotly.graph_objects as go
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFReportGenerator:
    """Generates comprehensive PDF reports."""
    
    def __init__(self, config: dict):
        """
        Initialize the PDF report generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Extract report configuration
        report_config = config.get('report', {})
        self.title_font_size = report_config.get('title_font_size', 24)
        self.heading_font_size = report_config.get('heading_font_size', 16)
        self.body_font_size = report_config.get('body_font_size', 11)
        self.page_margin = report_config.get('page_margin', 72)
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("PDFReportGenerator initialized")
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=self.title_font_size,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=self.heading_font_size,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=self.body_font_size,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
    
    def generate_report(
        self,
        output_path: Path,
        dataset_name: str,
        profile_results: Dict[str, Any],
        visualizations: List[tuple],  # List of (fig, spec) tuples
        insights: Dict[str, Any]
    ) -> Path:
        """
        Generate a comprehensive PDF report.
        
        Args:
            output_path: Path to save the PDF
            dataset_name: Name of the dataset
            profile_results: Profiling results dictionary
            visualizations: List of (Plotly figure, specification) tuples
            insights: Insights dictionary
            
        Returns:
            Path to the generated PDF
        """
        logger.info(f"Generating PDF report: {output_path}")
        
        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=self.page_margin,
            leftMargin=self.page_margin,
            topMargin=self.page_margin,
            bottomMargin=self.page_margin
        )
        
        # Build content
        story = []
        
        # Cover page
        story.extend(self._create_cover_page(dataset_name))
        story.append(PageBreak())
        
        # Dataset overview
        story.extend(self._create_overview_section(profile_results))
        story.append(Spacer(1, 0.3 * inch))
        
        # Data profiling
        story.extend(self._create_profiling_section(profile_results))
        story.append(PageBreak())
        
        # Visualizations
        story.extend(self._create_visualization_section(visualizations))
        
        # Insights
        story.extend(self._create_insights_section(insights))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated successfully: {output_path}")
        
        return output_path
    
    def _create_cover_page(self, dataset_name: str) -> List:
        """Create cover page elements."""
        elements = []
        
        # Title
        title = Paragraph(
            "Automated Data Insight Report",
            self.styles['CustomTitle']
        )
        elements.append(Spacer(1, 2 * inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))
        
        # Dataset name
        dataset_para = Paragraph(
            f"<b>Dataset:</b> {dataset_name}",
            self.styles['CustomHeading']
        )
        elements.append(dataset_para)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Generation date
        date_para = Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['CustomBody']
        )
        elements.append(date_para)
        
        return elements
    
    def _create_overview_section(self, profile_results: Dict[str, Any]) -> List:
        """Create dataset overview section."""
        elements = []
        
        # Section heading
        heading = Paragraph("Dataset Overview", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Overview table
        overview = profile_results.get('overview', {})
        data = [
            ['Metric', 'Value'],
            ['Total Rows', f"{overview.get('rows', 'N/A'):,}"],
            ['Total Columns', f"{overview.get('columns', 'N/A'):,}"],
            ['Memory Usage', f"{overview.get('memory_usage_mb', 0):.2f} MB"]
        ]
        
        table = Table(data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_profiling_section(self, profile_results: Dict[str, Any]) -> List:
        """Create data profiling section."""
        elements = []
        
        # Section heading
        heading = Paragraph("Data Profiling Summary", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Column types
        columns = profile_results.get('columns', {})
        col_data = [['Column Type', 'Count']]
        for col_type, col_list in columns.items():
            col_data.append([col_type.capitalize(), str(len(col_list))])
        
        col_table = Table(col_data, colWidths=[3 * inch, 3 * inch])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ]))
        
        elements.append(col_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Data quality
        quality = profile_results.get('data_quality', {})
        quality_para = Paragraph(
            f"<b>Data Quality:</b><br/>"
            f"• Duplicate rows: {quality.get('duplicate_rows', 0)} ({quality.get('duplicate_rows_pct', 0):.1f}%)<br/>"
            f"• Constant columns: {len(quality.get('constant_columns', []))}<br/>"
            f"• High missing columns: {len(quality.get('high_missing_columns', []))}",
            self.styles['CustomBody']
        )
        elements.append(quality_para)
        
        return elements
    
    def _create_visualization_section(self, visualizations: List[tuple]) -> List:
        """Create visualizations section."""
        elements = []
        
        # Section heading
        heading = Paragraph("Visualizations", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Add each visualization
        for idx, (fig, spec) in enumerate(visualizations):
            try:
                # Convert Plotly figure to image
                img_bytes = fig.to_image(format="png", width=600, height=400)
                img = Image(io.BytesIO(img_bytes), width=5.5 * inch, height=3.67 * inch)
                
                # Add caption
                caption = Paragraph(
                    f"<b>Figure {idx + 1}:</b> {spec.get('business_reason', 'N/A')}",
                    self.styles['CustomBody']
                )
                
                elements.append(img)
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(caption)
                elements.append(Spacer(1, 0.3 * inch))
                
                # Page break after every 2 plots
                if (idx + 1) % 2 == 0 and idx < len(visualizations) - 1:
                    elements.append(PageBreak())
            
            except Exception as e:
                logger.error(f"Error adding visualization {idx + 1}: {str(e)}")
                error_para = Paragraph(
                    f"<i>Error rendering visualization {idx + 1}</i>",
                    self.styles['CustomBody']
                )
                elements.append(error_para)
        
        elements.append(PageBreak())
        return elements
    
    def _create_insights_section(self, insights: Dict[str, Any]) -> List:
        """Create insights section."""
        elements = []
        
        # Section heading
        heading = Paragraph("Business Insights", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Get insights content
        content = insights.get('content', 'No insights available')
        
        # Convert markdown to paragraphs
        for line in content.split('\n'):
            if line.strip():
                if line.startswith('# '):
                    # Main heading
                    para = Paragraph(line.replace('# ', ''), self.styles['CustomHeading'])
                elif line.startswith('## '):
                    # Subheading
                    para = Paragraph(
                        f"<b>{line.replace('## ', '')}</b>",
                        self.styles['CustomBody']
                    )
                else:
                    # Body text
                    para = Paragraph(line, self.styles['CustomBody'])
                
                elements.append(para)
                elements.append(Spacer(1, 0.1 * inch))
        
        # Add metadata
        elements.append(Spacer(1, 0.3 * inch))
        metadata_para = Paragraph(
            f"<i>Word count: {insights.get('word_count', 'N/A')} | "
            f"Model: {insights.get('model', 'N/A')}</i>",
            self.styles['CustomBody']
        )
        elements.append(metadata_para)
        
        return elements
