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
        col = columns[0]
        
        # Get value counts
        value_counts = self.df[col].value_counts().head(20)  # Limit to top 20
        
        fig = go.Figure(data=[
            go.Bar(
                x=value_counts.index.astype(str),
                y=value_counts.values,
                marker_color=self.color_palette[0]
            )
        ])
        
        fig.update_layout(
            title=f'Distribution of {col}',
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
        
        return fig
    
    def _create_line_chart(self, columns: List[str], reason: str) -> go.Figure:
        """Create line chart for trend analysis."""
        fig = go.Figure()
        
        if len(columns) == 1:
            # Single line - use index as x-axis
            fig.add_trace(go.Scatter(
                x=self.df.index,
                y=self.df[columns[0]],
                mode='lines',
                name=columns[0],
                line=dict(color=self.color_palette[0])
            ))
            x_title = 'Index'
        else:
            # Two columns - first as x, second as y
            fig.add_trace(go.Scatter(
                x=self.df[columns[0]],
                y=self.df[columns[1]],
                mode='lines',
                name=columns[1],
                line=dict(color=self.color_palette[0])
            ))
            x_title = columns[0]
        
        fig.update_layout(
            title=f'Trend: {", ".join(columns)}',
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
        
        fig = go.Figure(data=[
            go.Scatter(
                x=clean_df[x_col],
                y=clean_df[y_col],
                mode='markers',
                marker=dict(
                    color=self.color_palette[0],
                    size=8,
                    opacity=0.6
                )
            )
        ])
        
        # Add trendline
        try:
            import numpy as np
            z = np.polyfit(clean_df[x_col], clean_df[y_col], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(clean_df[x_col].min(), clean_df[x_col].max(), 100)
            
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
        
        # Compute correlation matrix
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
