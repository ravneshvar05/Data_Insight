"""
Visualizations page for LLM-planned plots.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.visualization.planner import VisualizationPlanner
from src.visualization.plot_generator import PlotGenerator
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def show():
    """Display the visualizations page."""
    st.header("📈 Visualizations")
    
    # Check if dataset is loaded
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a dataset first.")
        return
    
    # Check if profiling is done
    if st.session_state.profile_results is None:
        st.warning("⚠️ Please run data profiling first.")
        st.info("👉 Navigate to **Data Profiling** to analyze your dataset.")
        return
    
    st.markdown(f"Creating visualizations for: **{st.session_state.dataset_name}**")
    
    # Generate visualizations if not already done
    if not st.session_state.visualizations:
        # User control for number of plots
        st.markdown("### ⚙️ Visualization Settings")
        num_plots = st.slider(
            "Number of plots to generate",
            min_value=5,
            max_value=15,
            value=8,
            help="Select how many business-focused visualizations you want to generate"
        )
        st.markdown("---")
        
        if st.button("🎨 Generate AI-Powered Visualizations", type="primary"):
            with st.spinner("Planning and generating visualizations... This may take a moment."):
                try:
                    config = get_config()
                    
                    # Plan visualizations using LLM with user-specified count
                    planner = VisualizationPlanner(
                        st.session_state.df,
                        st.session_state.profile_results,
                        config.all
                    )
                    plot_specs = planner.plan_visualizations(num_plots=num_plots)
                    
                    # Generate plots
                    generator = PlotGenerator(st.session_state.df, config.all)
                    visualizations = []
                    
                    for spec in plot_specs:
                        fig = generator.generate(spec)
                        visualizations.append((fig, spec))
                    
                    st.session_state.visualizations = visualizations
                    logger.info(f"Generated {len(visualizations)} visualizations")
                    st.success(f"✅ Generated {len(visualizations)} visualizations!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error generating visualizations: {str(e)}")
                    logger.error(f"Visualization error: {str(e)}")
        else:
            st.info("👆 Click the button above to generate visualizations powered by AI")
            st.markdown("""
            ### What will be generated?
            - 5-8 business-relevant visualizations
            - Automatically selected based on your data
            - ID/index columns are excluded
            - Focus on insights, trends, and patterns
            """)
        return
    
    # Display visualizations
    st.success(f"✅ {len(st.session_state.visualizations)} visualizations ready")
    
    # Show each visualization
    for idx, (fig, spec) in enumerate(st.session_state.visualizations):
        with st.container():
            st.markdown(f"### Visualization {idx + 1}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Type:** {spec['plot_type'].capitalize()}")
                st.markdown(f"**Columns:** {', '.join(spec['columns'])}")
            
            with col2:
                st.markdown(f"**Business Value:**")
            
            st.markdown(f"_{spec.get('business_reason', 'N/A')}_")
            
            # Display the plot
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
    
    # Regenerate option
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Regenerate Visualizations"):
            st.session_state.visualizations = []
            st.rerun()
