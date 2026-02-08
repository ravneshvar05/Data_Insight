"""
Plot generator using Plotly.
Generates actual visualizations based on LLM-planned specifications.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PlotGenerator:
    """Generates Plotly visualizations based on specifications."""
    
    def __init__(self, df: pd.DataFrame, config: dict):
        """
        Initialize the plot generator.
        
        Args:
            df: DataFrame to visualize
            config: Configuration dictionary
        """
        self.df = df
        self.config = config
        
        # Extract visualization config
        viz_config = config.get('visualization', {})
        self.theme = viz_config.get('default_theme', 'plotly_white')
        self.color_palette = viz_config.get('color_palette', px.colors.qualitative.Plotly)
        
        logger.info("PlotGenerator initialized")
    
    def generate(self, plot_spec: Dict[str, Any]) -> go.Figure:
        """
        Generate a plot based on specification.
        
        Args:
            plot_spec: Plot specification dictionary
            
        Returns:
            Plotly Figure object
        """
        plot_type = plot_spec.get('plot_type')
        columns = plot_spec.get('columns', [])
        business_reason = plot_spec.get('business_reason', '')
        
        logger.info(f"Generating {plot_type} plot for columns: {columns}")
        
        try:
            if plot_type == 'bar':
                fig = self._create_bar_chart(columns, business_reason)
            elif plot_type == 'line':
                fig = self._create_line_chart(columns, business_reason)
            elif plot_type == 'hist':
                fig = self._create_histogram(columns, business_reason)
            elif plot_type == 'box':
                fig = self._create_box_plot(columns, business_reason)
            elif plot_type == 'scatter':
                fig = self._create_scatter_plot(columns, business_reason)
            elif plot_type == 'heatmap':
                fig = self._create_heatmap(columns, business_reason)
            else:
                logger.warning(f"Unknown plot type: {plot_type}, creating histogram as fallback")
                fig = self._create_histogram(columns, business_reason)
            
            # Apply theme
            fig.update_layout(template=self.theme)
            
            return fig
        
        except Exception as e:
            logger.error(f"Error generating plot: {str(e)}")
            # Return empty figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error generating plot: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def _create_bar_chart(self, columns: List[str], reason: str) -> go.Figure:
        """Create bar chart for categorical data."""
        
        if len(columns) == 1:
            # Single column - count distribution
            col = columns[0]
            value_counts = self.df[col].value_counts().head(20)  # Limit to top 20
            
            fig = go.Figure(data=[
                go.Bar(
                    x=value_counts.index.astype(str),
                    y=value_counts.values,
                    marker_color=self.color_palette[0]
                )
            ])
            
            fig.update_layout(
                title=f'Distribution of {col} (Top 20)',
                xaxis_title=col,
                yaxis_title='Count',
                annotations=[{
                    'text': reason,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': -0.15,
                    'showarrow': False,
                    'font': {'size': 10, 'color': 'gray'},
                    'xanchor': 'center'
                }]
            )
        else:
            # Two columns - CRITICAL: Detect which is category and which is metric
            col1, col2 = columns[0], columns[1]
            
            # Determine which is categorical and which is numeric
            col1_is_numeric = pd.api.types.is_numeric_dtype(self.df[col1])
            col2_is_numeric = pd.api.types.is_numeric_dtype(self.df[col2])
            col1_nunique = self.df[col1].nunique()
            col2_nunique = self.df[col2].nunique()
            
            # Logic: Category column has fewer unique values OR is non-numeric
            if (not col1_is_numeric) or (col1_is_numeric and col2_is_numeric and col1_nunique < col2_nunique):
                # col1 is category, col2 is metric
                category_col = col1
                metric_col = col2
            else:
                # col2 is category, col1 is metric
                category_col = col2
                metric_col = col1
            
            # Aggregate metric by category (sum)
            aggregated = self.df.groupby(category_col)[metric_col].sum().sort_values(ascending=False).head(20)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=aggregated.index.astype(str),
                    y=aggregated.values,
                    marker_color=self.color_palette[0]
                )
            ])
            
            fig.update_layout(
                title=f'{metric_col} by {category_col} (Top 20)',
                xaxis_title=category_col,
                yaxis_title=f'Total {metric_col}',
                annotations=[{
                    'text': reason,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': -0.15,
                    'showarrow': False,
                    'font': {'size': 10, 'color': 'gray'},
                    'xanchor': 'center'
                }]
            )
        
        return fig
    
    def _create_line_chart(self, columns: List[str], reason: str) -> go.Figure:
        """Create line chart for trend analysis."""
        fig = go.Figure()
        
        # Use WebGL (Scattergl) if dataset is large (>5000 rows)
        # This allows rendering all data points without browser hanging
        use_webgl = len(self.df) > 5000
        ScatterClass = go.Scattergl if use_webgl else go.Scatter
        
        if len(columns) == 1:
            # Single line - use index as x-axis
            fig.add_trace(ScatterClass(
                x=self.df.index,
                y=self.df[columns[0]],
                mode='lines',
                name=columns[0],
                line=dict(color=self.color_palette[0])
            ))
            x_title = 'Index'
            title = f'{columns[0]} Trend'
        else:
            # Two columns - intelligently determine X (Date) and Y (Metric)
            col1, col2 = columns[0], columns[1]
            
            # Helper to check if a column looks like a date
            def is_potential_date(series):
                if pd.api.types.is_datetime64_any_dtype(series):
                    return True
                if pd.api.types.is_object_dtype(series):
                    # Check first non-null value
                    val = series.dropna().iloc[0] if not series.dropna().empty else ""
                    return isinstance(val, str) and (val.count('-') >= 2 or val.count('/') >= 2)
                return False

            # Determine X and Y axes
            # We want Date on X-axis and Metric on Y-axis
            col1_is_date = is_potential_date(self.df[col1])
            col2_is_date = is_potential_date(self.df[col2])
            
            if col1_is_date and not col2_is_date:
                x_col, y_col = col1, col2
            elif col2_is_date and not col1_is_date:
                x_col, y_col = col2, col1
            else:
                # Fallback: simple assignment or heuristic
                # If neither or both are dates, assume first is X
                x_col, y_col = col1, col2
            
            # SMART TIME AGGREGATION: Check if x-axis is datetime
            df_plot = self.df.copy()
            
            # Try to detect and parse datetime column
            if pd.api.types.is_object_dtype(df_plot[x_col]):
                try:
                    # Try with dayfirst=True for international formats (DD-MM-YYYY)
                    df_plot[x_col] = pd.to_datetime(df_plot[x_col], dayfirst=True, errors='coerce')
                except:
                    # Fallback to default
                    try:
                        df_plot[x_col] = pd.to_datetime(df_plot[x_col], errors='coerce')
                    except:
                        pass
            
            # Check if we successfully converted to datetime
            is_datetime = pd.api.types.is_datetime64_any_dtype(df_plot[x_col])
            
            # Aggregate by month if datetime detected
            if is_datetime:
                # Remove NaT values
                df_plot = df_plot.dropna(subset=[x_col])
                
                if not df_plot.empty:
                    # Create month column
                    df_plot['_month'] = df_plot[x_col].dt.to_period('M')
                    
                    # Aggregate by month (sum for metrics)
                    monthly_data = df_plot.groupby('_month')[y_col].sum().reset_index()
                    monthly_data['_month'] = monthly_data['_month'].dt.to_timestamp()
                    
                    fig.add_trace(ScatterClass(
                        x=monthly_data['_month'],
                        y=monthly_data[y_col],
                        mode='lines+markers',
                        name=y_col,
                        line=dict(color=self.color_palette[0], width=2),
                        marker=dict(size=6)
                    ))
                    x_title = f'{x_col} (Monthly)'
                    title = f'{y_col} over {x_col} (Monthly Trend)'
                    
                    logger.info(f"Aggregated {len(df_plot)} daily records to {len(monthly_data)} monthly points")
                else:
                    is_datetime = False
            
            if not is_datetime:
                # If NOT datetime (or parsing failed), plot generic line chart
                # Sort by x axis to prevent messy lines (for numeric data)
                if pd.api.types.is_numeric_dtype(df_plot[x_col]):
                    df_plot = df_plot.sort_values(by=x_col)
                
                fig.add_trace(ScatterClass(
                    x=df_plot[x_col],
                    y=df_plot[y_col],
                    mode='lines',
                    name=y_col,
                    line=dict(color=self.color_palette[0])
                ))
                x_title = x_col
                title = f'{y_col} over {x_col}'
        
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title=columns[-1],
            annotations=[{
                'text': reason,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.15,
                'showarrow': False,
                'font': {'size': 10, 'color': 'gray'},
                'xanchor': 'center'
            }]
        )
        
        return fig
    
    def _create_histogram(self, columns: List[str], reason: str) -> go.Figure:
        """Create histogram for distribution analysis."""
        col = columns[0]
        
        # Histogram aggregates data into bins, so we can send all data
        # unless it's extremely large (>500k), in which case we might need server-side binning.
        # For 80k rows, client-side binning is fine.
        
        fig = go.Figure(data=[
            go.Histogram(
                x=self.df[col].dropna(),
                nbinsx=30,
                marker_color=self.color_palette[0]
            )
        ])
        
        fig.update_layout(
            title=f'Distribution of {col}',
            xaxis_title=col,
            yaxis_title='Frequency',
            annotations=[{
                'text': reason,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.15,
                'showarrow': False,
                'font': {'size': 10, 'color': 'gray'},
                'xanchor': 'center'
            }]
        )
        
        return fig
    
    def _create_box_plot(self, columns: List[str], reason: str) -> go.Figure:
        """Create box plot for outlier detection."""
        fig = go.Figure()
        
        for idx, col in enumerate(columns[:5]):  # Limit to 5 columns
            fig.add_trace(go.Box(
                y=self.df[col].dropna(),
                name=col,
                marker_color=self.color_palette[idx % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title=f'Box Plot: {", ".join(columns[:5])}',
            yaxis_title='Value',
            annotations=[{
                'text': reason,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.15,
                'showarrow': False,
                'font': {'size': 10, 'color': 'gray'},
                'xanchor': 'center'
            }]
        )
        
        return fig
    
    def _create_scatter_plot(self, columns: List[str], reason: str) -> go.Figure:
        """Create scatter plot for correlation analysis."""
        if len(columns) < 2:
            # Fallback to histogram if not enough columns
            return self._create_histogram(columns, reason)
        
        x_col, y_col = columns[0], columns[1]
        
        # Clean data - remove rows with NaN in either column
        clean_df = self.df[[x_col, y_col]].dropna()
        
        # Use WebGL (Scattergl) if dataset is large
        use_webgl = len(clean_df) > 5000
        ScatterClass = go.Scattergl if use_webgl else go.Scatter
        
        fig = go.Figure(data=[
            ScatterClass(
                x=clean_df[x_col],
                y=clean_df[y_col],
                mode='markers',
                marker=dict(
                    color=self.color_palette[0],
                    size=6,
                    opacity=0.6
                )
            )
        ])
        
        # Add trendline (calculate on full data)
        try:
            import numpy as np
            z = np.polyfit(clean_df[x_col], clean_df[y_col], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(clean_df[x_col].min(), clean_df[x_col].max(), 100)
            
            # Trendline is simple (100 points), so standard Scatter is fine
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=p(x_trend),
                mode='lines',
                name='Trend',
                line=dict(color='red', dash='dash')
            ))
        except:
            pass
        
        fig.update_layout(
            title=f'Correlation: {x_col} vs {y_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            annotations=[{
                'text': reason,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.15,
                'showarrow': False,
                'font': {'size': 10, 'color': 'gray'},
                'xanchor': 'center'
            }]
        )
        
        return fig
    
    def _create_heatmap(self, columns: List[str], reason: str) -> go.Figure:
        """Create correlation heatmap."""
        # Use only numeric columns
        numeric_cols = []
        for col in columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                numeric_cols.append(col)
        
        if len(numeric_cols) < 2:
            return self._create_histogram(columns, "Not enough numeric columns for heatmap")
        
        # Compute correlation matrix (always fast as it aggregates)
        corr_matrix = self.df[numeric_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title='Correlation Heatmap',
            annotations=[{
                'text': reason,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': -0.15,
                'showarrow': False,
                'font': {'size': 10, 'color': 'gray'},
                'xanchor': 'center'
            }]
        )
        
        return fig
