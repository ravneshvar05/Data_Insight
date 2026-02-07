"""
Visualization planner using LLM to decide which plots to create.
LLM determines WHAT to visualize, not HOW to compute the data.
"""

import pandas as pd
from typing import Dict, List, Any
from src.llm.groq_client import GroqClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisualizationPlanner:
    """Uses LLM to plan business-relevant visualizations."""
    
    def __init__(self, df: pd.DataFrame, profile_results: Dict[str, Any], config: dict):
        """
        Initialize the visualization planner.
        
        Args:
            df: Original DataFrame
            profile_results: Results from DataProfiler
            config: Configuration dictionary
        """
        self.df = df
        self.profile_results = profile_results
        self.config = config
        self.llm_client = GroqClient(config)
        
        # Extract configuration
        viz_config = config.get('visualization', {})
        self.min_plots = viz_config.get('min_plots', 5)
        self.max_plots = viz_config.get('max_plots', 8)
        
        logger.info("VisualizationPlanner initialized")
    
    def plan_visualizations(self) -> List[Dict[str, Any]]:
        """
        Use LLM to plan visualizations.
        
        Returns:
            List of plot specifications
        """
        logger.info("Planning visualizations using LLM...")
        
        # Prepare data for LLM
        schema = self._prepare_schema()
        correlations = self.profile_results.get('correlations', {}).get('strong_correlations', [])
        sample_data = self._get_sample_data()
        id_columns = self.profile_results.get('columns', {}).get('id', [])
        
        # Call LLM
        try:
            result = self.llm_client.generate_visualization_plan(
                schema=schema,
                correlations=correlations,
                sample_data=sample_data,
                id_columns=id_columns
            )
            
            # Extract plot specifications
            plots = result['content'].get('plots', [])
            
            # Validate plots
            valid_plots = self._validate_plots(plots)
            
            # Ensure we have minimum number of plots
            if len(valid_plots) < self.min_plots:
                logger.warning(f"LLM returned only {len(valid_plots)} plots, expected at least {self.min_plots}")
                # Add basic plots if needed
                valid_plots.extend(self._get_fallback_plots(self.min_plots - len(valid_plots)))
            
            # Limit to max plots
            if len(valid_plots) > self.max_plots:
                valid_plots = valid_plots[:self.max_plots]
            
            logger.info(f"Successfully planned {len(valid_plots)} visualizations")
            return valid_plots
        
        except Exception as e:
            logger.error(f"Error planning visualizations: {str(e)}")
            logger.info("Falling back to default visualization plan")
            return self._get_fallback_plots(self.min_plots)
    
    def _prepare_schema(self) -> Dict[str, Any]:
        """Prepare schema information for LLM."""
        columns = self.profile_results.get('columns', {})
        
        schema = {
            'total_columns': len(self.df.columns),
            'total_rows': len(self.df),
            'column_types': {}
        }
        
        # Add column information
        for col_type, col_list in columns.items():
            for col in col_list:
                schema['column_types'][col] = col_type
        
        return schema
    
    def _get_sample_data(self) -> str:
        """Get sample data rows as string."""
        # Exclude ID columns
        id_columns = self.profile_results.get('columns', {}).get('id', [])
        display_columns = [col for col in self.df.columns if col not in id_columns]
        
        # Get first 3 rows
        sample = self.df[display_columns].head(3)
        return sample.to_string()
    
    def _validate_plots(self, plots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate plot specifications from LLM.
        
        Args:
            plots: List of plot specifications
            
        Returns:
            List of valid plot specifications
        """
        valid_plots = []
        valid_plot_types = ['bar', 'line', 'hist', 'box', 'scatter', 'heatmap']
        id_columns = self.profile_results.get('columns', {}).get('id', [])
        
        for plot in plots:
            # Check required fields
            if 'plot_type' not in plot or 'columns' not in plot:
                logger.warning(f"Skipping invalid plot specification: {plot}")
                continue
            
            # Check plot type
            if plot['plot_type'] not in valid_plot_types:
                logger.warning(f"Skipping unsupported plot type: {plot['plot_type']}")
                continue
            
            # Check columns exist and are not ID columns
            columns = plot['columns']
            if not isinstance(columns, list):
                columns = [columns]
            
            # Filter out ID columns
            columns = [col for col in columns if col in self.df.columns and col not in id_columns]
            
            if len(columns) == 0:
                logger.warning(f"Skipping plot with no valid columns: {plot}")
                continue
            
            # Update plot with validated columns
            plot['columns'] = columns
            valid_plots.append(plot)
        
        return valid_plots
    
    def _get_fallback_plots(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate fallback plot specifications if LLM fails.
        
        Args:
            count: Number of plots to generate
            
        Returns:
            List of plot specifications
        """
        logger.info(f"Generating {count} fallback plots")
        
        fallback_plots = []
        columns = self.profile_results.get('columns', {})
        numeric_cols = [col for col in columns.get('numeric', []) if col not in columns.get('id', [])]
        categorical_cols = [col for col in columns.get('categorical', []) if col not in columns.get('id', [])]
        
        # Histogram for first numeric column
        if numeric_cols and len(fallback_plots) < count:
            fallback_plots.append({
                'plot_type': 'hist',
                'columns': [numeric_cols[0]],
                'business_reason': f'Distribution analysis of {numeric_cols[0]}'
            })
        
        # Box plot for numeric columns
        if len(numeric_cols) >= 2 and len(fallback_plots) < count:
            fallback_plots.append({
                'plot_type': 'box',
                'columns': numeric_cols[:3],
                'business_reason': 'Comparison of distributions and outlier detection'
            })
        
        # Bar chart for categorical
        if categorical_cols and len(fallback_plots) < count:
            fallback_plots.append({
                'plot_type': 'bar',
                'columns': [categorical_cols[0]],
                'business_reason': f'Frequency analysis of {categorical_cols[0]}'
            })
        
        # Scatter plot for correlated numeric columns
        correlations = self.profile_results.get('correlations', {}).get('strong_correlations', [])
        if correlations and len(fallback_plots) < count:
            corr = correlations[0]
            fallback_plots.append({
                'plot_type': 'scatter',
                'columns': [corr['column1'], corr['column2']],
                'business_reason': f"Correlation analysis between {corr['column1']} and {corr['column2']}"
            })
        
        # Correlation heatmap
        if len(numeric_cols) >= 3 and len(fallback_plots) < count:
            fallback_plots.append({
                'plot_type': 'heatmap',
                'columns': numeric_cols[:5],
                'business_reason': 'Overall correlation matrix visualization'
            })
        
        return fallback_plots[:count]
