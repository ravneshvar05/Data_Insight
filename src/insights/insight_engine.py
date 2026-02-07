"""
Insight engine for generating business insights using LLM.
Uses stronger model for detailed, actionable insights.
"""

from typing import Dict, List, Any
from src.llm.groq_client import GroqClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InsightEngine:
    """Generates comprehensive business insights using LLM."""
    
    def __init__(self, profile_results: Dict[str, Any], config: dict):
        """
        Initialize the insight engine.
        
        Args:
            profile_results: Results from DataProfiler
            config: Configuration dictionary
        """
        self.profile_results = profile_results
        self.config = config
        self.llm_client = GroqClient(config)
        
        # Extract configuration
        insights_config = config.get('insights', {})
        self.min_words = insights_config.get('min_words', 800)
        self.max_words = insights_config.get('max_words', 1200)
        self.sections = insights_config.get('sections', [
            'Executive Summary',
            'Key Insights',
            'Risks & Anomalies',
            'Opportunities',
            'Actionable Recommendations'
        ])
        
        logger.info("InsightEngine initialized")
    
    def generate_insights(self, visualizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive business insights.
        
        Args:
            visualizations: List of visualization specifications
            
        Returns:
            Dictionary with insights content and metadata
        """
        logger.info("Generating business insights using LLM...")
        
        try:
            # Get ID columns to exclude from insights
            id_columns = self.profile_results.get('columns', {}).get('id', [])
            
            # Call LLM
            result = self.llm_client.generate_insights(
                profile_data=self.profile_results,
                visualizations=visualizations,
                id_columns=id_columns
            )
            
            # Extract insights
            insights_text = result['content']
            
            # Validate insights
            word_count = len(insights_text.split())
            logger.info(f"Generated insights with {word_count} words")
            
            if word_count < self.min_words * 0.7:
                logger.warning(f"Insights are shorter than expected ({word_count} < {self.min_words})")
            
            return {
                'content': insights_text,
                'word_count': word_count,
                'model': result['model'],
                'tokens': result['tokens'],
                'sections': self._extract_sections(insights_text)
            }
        
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                'content': self._get_fallback_insights(),
                'word_count': 0,
                'error': str(e)
            }
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract sections from markdown text.
        
        Args:
            text: Markdown text with headers
            
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            # Check if line is a header
            if line.startswith('# '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.replace('# ', '').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _get_fallback_insights(self) -> str:
        """Generate basic fallback insights if LLM fails."""
        
        overview = self.profile_results.get('overview', {})
        quality = self.profile_results.get('data_quality', {})
        correlations = self.profile_results.get('correlations', {}).get('strong_correlations', [])
        
        insights = f"""# Executive Summary

Unable to generate detailed LLM-powered insights at this time. Below is a basic statistical summary.

The dataset contains {overview.get('rows', 'N/A')} rows and {overview.get('columns', 'N/A')} columns, 
using approximately {overview.get('memory_usage_mb', 0):.2f} MB of memory.

# Key Insights

## Data Quality
- Duplicate rows: {quality.get('duplicate_rows', 0)} ({quality.get('duplicate_rows_pct', 0):.1f}%)
- Constant columns: {len(quality.get('constant_columns', []))}
- Columns with high missing values: {len(quality.get('high_missing_columns', []))}

## Correlations
"""
        
        if correlations:
            insights += "\nStrong correlations found:\n"
            for corr in correlations[:3]:
                insights += f"- {corr['column1']} and {corr['column2']}: {corr['correlation']:.2f} ({corr['strength']})\n"
        else:
            insights += "\nNo strong correlations detected in the data.\n"
        
        insights += """
# Recommendations

1. Review data quality issues, especially duplicate rows and missing values
2. Investigate strong correlations for business opportunities
3. Consider data cleaning for constant or high-missing columns
4. Perform deeper domain-specific analysis based on business goals
"""
        
        return insights
