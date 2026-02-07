"""
Groq API client wrapper for LLM interactions.
Provides structured interface for visualization planning and insight generation.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from groq import Groq
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Wrapper for Groq API with retry logic and error handling."""
    
    def __init__(self, config: dict):
        """
        Initialize Groq client.
        
        Args:
            config: Configuration dictionary
        """
        llm_config = config.get('llm', {})
        
        # Get API key
        api_key = llm_config.get('api_key') or os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Please set it in .env file or environment variables. "
                "Get your API key from: https://console.groq.com/keys"
            )
        
        self.client = Groq(api_key=api_key)
        
        # Configuration
        self.viz_model = llm_config.get('visualization_model', 'llama-3.1-8b-instant')
        self.insight_model = llm_config.get('insight_model', 'llama-3.3-70b-versatile')
        self.max_tokens = llm_config.get('max_tokens', 4096)
        self.temperature = llm_config.get('temperature', 0.3)
        self.timeout = llm_config.get('timeout', 30)
        self.max_retries = llm_config.get('max_retries', 3)
        
        logger.info(f"GroqClient initialized with viz_model={self.viz_model}, insight_model={self.insight_model}")
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        response_format: str = "text",
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate completion from Groq API.
        
        Args:
            prompt: The prompt to send
            model: Model to use (defaults to visualization model)
            response_format: 'text' or 'json'
            temperature: Override default temperature
            
        Returns:
            Dictionary with 'content', 'model', 'tokens' keys
        """
        if model is None:
            model = self.viz_model
        
        if temperature is None:
            temperature = self.temperature
        
        logger.info(f"Generating completion with model={model}, format={response_format}")
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Prepare messages
                messages = [{"role": "user", "content": prompt}]
                
                # Make API call
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout
                )
                
                # Extract content
                content = response.choices[0].message.content
                
                # Parse JSON if requested
                if response_format == "json":
                    try:
                        content = self._parse_json_response(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        if attempt < self.max_retries - 1:
                            logger.info(f"Retrying... (attempt {attempt + 2}/{self.max_retries})")
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            raise ValueError(f"Failed to parse JSON response after {self.max_retries} attempts")
                
                # Return result
                result = {
                    'content': content,
                    'model': model,
                    'tokens': {
                        'prompt': response.usage.prompt_tokens,
                        'completion': response.usage.completion_tokens,
                        'total': response.usage.total_tokens
                    }
                }
                
                logger.info(f"Generation successful. Tokens used: {result['tokens']['total']}")
                return result
            
            except Exception as e:
                logger.error(f"Error generating completion (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Failed to generate completion after {self.max_retries} attempts: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response with robust error handling.
        
        Args:
            response: Raw response string
            
        Returns:
            Parsed JSON dictionary
        """
        # Try to extract JSON from markdown code blocks
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            response = response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            response = response[start:end].strip()
        
        # Parse JSON
        return json.loads(response)
    
    def generate_visualization_plan(
        self,
        schema: Dict[str, Any],
        correlations: list,
        sample_data: str,
        id_columns: list
    ) -> Dict[str, Any]:
        """
        Generate visualization plan using LLM.
        
        Args:
            schema: Dataset schema information
            correlations: List of strong correlations
            sample_data: Sample rows as string
            id_columns: List of ID columns to exclude
            
        Returns:
            Visualization plan dictionary
        """
        prompt = self._build_visualization_prompt(schema, correlations, sample_data, id_columns)
        
        result = self.generate(
            prompt=prompt,
            model=self.viz_model,
            response_format="json",
            temperature=0.3
        )
        
        return result
    
    def generate_insights(
        self,
        profile_data: Dict[str, Any],
        visualizations: list,
        id_columns: list
    ) -> Dict[str, Any]:
        """
        Generate business insights using LLM.
        
        Args:
            profile_data: Profiling results
            visualizations: List of visualization descriptions
            id_columns: List of ID columns to exclude
            
        Returns:
            Insights dictionary
        """
        prompt = self._build_insights_prompt(profile_data, visualizations, id_columns)
        
        result = self.generate(
            prompt=prompt,
            model=self.insight_model,
            response_format="text",
            temperature=0.3
        )
        
        return result
    
    def _build_visualization_prompt(
        self,
        schema: Dict[str, Any],
        correlations: list,
        sample_data: str,
        id_columns: list
    ) -> str:
        """Build prompt for visualization planning."""
        
        id_columns_str = ', '.join(id_columns) if id_columns else 'None'
        correlations_str = json.dumps(correlations[:10], indent=2) if correlations else 'No strong correlations found'
        
        prompt = f"""You are a data visualization expert. Based on the dataset schema and statistics, recommend 5-8 business-relevant visualizations.

STRICT RULES:
1. EXCLUDE these ID/index columns: {id_columns_str}
2. Focus on business insights, not technical metadata
3. Prefer: trends, distributions, comparisons, contributions, correlations
4. Each plot must have a clear business purpose
5. Use maximum 2 columns per plot
6. Recommend between 5 and 8 plots total

Dataset Schema:
{json.dumps(schema, indent=2)}

Strong Correlations:
{correlations_str}

Sample Data (first 3 rows):
{sample_data}

Return ONLY valid JSON in this exact format (no other text):
{{
  "plots": [
    {{
      "plot_type": "bar|line|hist|box|scatter|heatmap",
      "columns": ["col1"] or ["col1", "col2"],
      "business_reason": "concise explanation of business value"
    }}
  ]
}}

Ensure:
- bar: for categorical comparisons
- line: for trends over time or sequences
- hist: for distribution of numeric values
- box: for outlier detection and distribution comparison
- scatter: for correlation between two numeric variables
- heatmap: for correlation matrix visualization
"""
        
        return prompt
    
    def _build_insights_prompt(
        self,
        profile_data: Dict[str, Any],
        visualizations: list,
        id_columns: list
    ) -> str:
        """Build prompt for insight generation."""
        
        id_columns_str = ', '.join(id_columns) if id_columns else 'None'
        
        # Extract key information
        overview = profile_data.get('overview', {})
        correlations = profile_data.get('correlations', {}).get('strong_correlations', [])
        quality = profile_data.get('data_quality', {})
        
        # Sample statistics
        stats_summary = {}
        for col, stats in profile_data.get('numeric_stats', {}).items():
            stats_summary[col] = {
                'mean': stats.get('mean'),
                'std': stats.get('std'),
                'min': stats.get('min'),
                'max': stats.get('max'),
                'outliers': stats.get('outlier_count', 0)
            }
        
        viz_summary = '\n'.join([f"- {v.get('plot_type', 'unknown')}: {v.get('columns', [])} - {v.get('business_reason', 'N/A')}" 
                                  for v in visualizations])
        
        prompt = f"""You are a senior business analyst. Generate comprehensive, actionable insights from this dataset analysis.

STRICT RULES:
1. NO insights about ID/index columns: {id_columns_str}
2. NO fabricated numbers - use ONLY the provided statistics
3. Output length: 800-1200 words
4. Format: Markdown with clear sections
5. Focus on business impact and actionability
6. Be specific with numbers from the data

Dataset Overview:
- Rows: {overview.get('rows', 'N/A')}
- Columns: {overview.get('columns', 'N/A')}
- Memory: {overview.get('memory_usage_mb', 0):.2f} MB

Key Statistics:
{json.dumps(stats_summary, indent=2)}

Strong Correlations (>{profile_data.get('correlations', {}).get('threshold', 0.6)}):
{json.dumps(correlations[:5], indent=2)}

Data Quality Issues:
- Duplicate rows: {quality.get('duplicate_rows', 0)} ({quality.get('duplicate_rows_pct', 0):.1f}%)
- Constant columns: {len(quality.get('constant_columns', []))}
- High missing columns: {len(quality.get('high_missing_columns', []))}

Visualizations Created:
{viz_summary}

Generate insights with these sections (use Markdown headers):

# Executive Summary
(2-3 paragraphs summarizing the most important findings)

# Key Insights
(3-5 numbered insights with specific data points)

# Risks & Anomalies
(Data quality issues, outliers, potential problems)

# Opportunities
(Patterns that suggest business opportunities)

# Actionable Recommendations
(Specific, concrete recommendations based on the data)

Remember: Be specific, cite numbers, avoid generic statements, focus on business value.
"""
        
        return prompt
