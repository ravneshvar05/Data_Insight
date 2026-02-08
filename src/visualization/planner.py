import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from ..llm.groq_client import GroqClient

logger = logging.getLogger(__name__)

class VisualizationPlanner:
    """Planning engine for data visualizations."""
    
    def __init__(self, df: pd.DataFrame, profile_results: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Initialize the planner.
        
        Args:
            df: The dataframe to visualize
            profile_results: Data profiling results
            config: Configuration dictionary
        """
        self.df = df
        self.profile_results = profile_results
        self.config = config or {}
        # Pass config to GroqClient if needed, or use default
        self.llm_client = GroqClient(self.config) if self.config else GroqClient()
        self.max_plots = 15
        self.min_plots = 5
        
    def _prepare_schema(self) -> str:
        """Prepare simplified schema for LLM."""
        columns = self.profile_results.get('columns', {})
        
        schema = "Dataset Schema:\n"
        
        # Numeric columns
        if columns.get('numeric'):
            schema += f"Numeric Columns: {', '.join(columns['numeric'])}\n"
            
        # Categorical columns
        if columns.get('categorical'):
            # Add cardinality for categorical columns
            cat_info = []
            for col in columns['categorical']:
                unique_count = self.df[col].nunique()
                cat_info.append(f"{col} ({unique_count} unique values)")
            schema += f"Categorical Columns: {', '.join(cat_info)}\n"
            
        # Date columns
        if columns.get('date'):
            schema += f"Date/Time Columns: {', '.join(columns['date'])}\n"
            
        return schema
        
    def _get_sample_data(self) -> str:
        """Get string representation of sample data."""
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
        seen_plots = set()  # Track duplicates
        
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
            
            # DEDUPLICATION: Skip duplicate plots
            plot_signature = f"{plot['plot_type']}_{'-'.join(sorted(columns))}"
            if plot_signature in seen_plots:
                logger.warning(f"Skipping duplicate plot: {plot['plot_type']} with {columns}")
                continue
            seen_plots.add(plot_signature)
            
            # CRITICAL: Validate single-category bar plots
            # Check ALL columns involved in the plot
            is_single_category = False
            if plot['plot_type'] == 'bar':
                for col in columns:
                    # If any column used in a bar chart has only 1 unique value, it creates a useless plot
                    if col in self.df.columns and self.df[col].nunique() <= 1:
                        logger.warning(f"Skipping bar plot for '{col}' - only 1 unique value")
                        is_single_category = True
                        break
            
            if is_single_category:
                continue
            
            # CRITICAL: Validate line charts for readability
            # Line charts with too many categories become unreadable
            if plot['plot_type'] == 'line' and len(columns) >= 2:
                # Check for categorical columns that would create too many lines
                categorical_cols = self.profile_results.get('columns', {}).get('categorical', [])
                
                for col in columns:
                    if col in categorical_cols:
                        unique_count = self.df[col].nunique()
                        # Limit to 10 categories max for line charts
                        if unique_count > 10:
                            logger.warning(f"Skipping line plot - '{col}' has {unique_count} categories (max 10 for readability)")
                            # We don't skip here, because the generator now handles limiting!
                            pass
            
            # Update plot with validated columns
            plot['columns'] = columns
            valid_plots.append(plot)
        
        logger.info(f"Validated {len(valid_plots)} unique plots from {len(plots)} suggestions")
        return valid_plots
    
    def _get_fallback_plots(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate fallback plot specifications if LLM fails or returns too few plots.
        
        Args:
            count: Number of plots to generate
        
        Returns:
            List of fallback plot specifications
        """
        plots = []
        numeric_cols = self.profile_results.get('columns', {}).get('numeric', [])
        categorical_cols = self.profile_results.get('columns', {}).get('categorical', [])
        date_cols = self.profile_results.get('columns', {}).get('date', [])
        
        # Iterative generation to reach count
        # We cycle through different strategies to fill the request
        attempts = 0
        while len(plots) < count and attempts < 3:
            attempts += 1
            
            # Priority 1: Numeric distributions (Histogram for first pass, Box for second)
            for col in numeric_cols:
                if len(plots) >= count: break
                plot_type = 'hist' if attempts == 1 else 'box'
                # Check if we already have this plot
                is_duplicate = any(p['plot_type'] == plot_type and p['columns'] == [col] for p in plots)
                if not is_duplicate:
                    plots.append({
                        "plot_type": plot_type,
                        "columns": [col],
                        "business_reason": f"Analyze distribution of {col}"
                    })
            
            # Priority 2: Categorical counts (Bar) - ONLY if >1 category
            for col in categorical_cols:
                if len(plots) >= count: break
                if self.df[col].nunique() > 1:
                    is_duplicate = any(p['plot_type'] == 'bar' and p['columns'] == [col] for p in plots)
                    if not is_duplicate:
                        plots.append({
                            "plot_type": "bar",
                            "columns": [col],
                            "business_reason": f"Compare counts across {col}"
                        })
            
            # Priority 3: Numeric vs Categorical (Bar) - ONLY if >1 category
            if numeric_cols and categorical_cols:
                num_col = numeric_cols[0]
                for cat_col in categorical_cols:
                    if len(plots) >= count: break
                    if self.df[cat_col].nunique() > 1:
                        # Logic to avoid duplicates can be added here
                        plots.append({
                            "plot_type": "bar",
                            "columns": [cat_col, num_col],
                            "business_reason": f"Analyze {num_col} by {cat_col}"
                        })
                    
            # Priority 4: Time series (Line)
            if date_cols and numeric_cols:
                date_col = date_cols[0]
                for num_col in numeric_cols:
                    if len(plots) >= count: break
                    plots.append({
                        "plot_type": "line",
                        "columns": [date_col, num_col],
                        "business_reason": f"Track {num_col} over {date_col}"
                    })
        
        return plots[:count]

    def plan_visualizations(self, num_plots: int = None) -> List[Dict[str, Any]]:
        """
        Use LLM to plan visualizations.
        
        Args:
            num_plots: Number of plots to generate (if None, uses default from config)
        
        Returns:
            List of plot specifications
        """
        logger.info("Planning visualizations using LLM...")
        
        # Use provided num_plots or default from config
        target_plots = num_plots if num_plots is not None else self.max_plots
        
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
                id_columns=id_columns,
                num_plots=target_plots
            )
            
            # Extract plot specifications
            plots = result['content'].get('plots', [])
            
            # Validate plots
            valid_plots = self._validate_plots(plots)
            
            # Ensure we have target number of plots
            if len(valid_plots) < target_plots:
                logger.warning(f"LLM returned only {len(valid_plots)} valid plots from {len(plots)} suggestions, expected {target_plots}")
                # Add fallback plots to fill the gap
                needed = target_plots - len(valid_plots)
                fallback = self._get_fallback_plots(needed)
                valid_plots.extend(fallback)
            
            # Limit to requested number of plots
            if len(valid_plots) > target_plots:
                valid_plots = valid_plots[:target_plots]
            
            logger.info(f"Successfully planned {len(valid_plots)} visualizations")
            return valid_plots
        
        except Exception as e:
            logger.error(f"Error planning visualizations: {str(e)}")
            logger.info("Falling back to default visualization plan")
            return self._get_fallback_plots(target_plots)
