"""
Insights page for LLM-generated business insights.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.insights.insight_engine import InsightEngine
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def show():
    """Display the insights page."""
    st.header("💡 Business Insights")
    
    # Check if dataset is loaded
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a dataset first.")
        return
    
    # Check if profiling is done
    if st.session_state.profile_results is None:
        st.warning("⚠️ Please run data profiling first.")
        st.info("👉 Navigate to **Data Profiling** to analyze your dataset.")
        return
    
    # Check if visualizations are generated
    if not st.session_state.visualizations:
        st.warning("⚠️ Please generate visualizations first.")
        st.info("👉 Navigate to **Visualizations** to create charts.")
        return
    
    st.markdown(f"Generating insights for: **{st.session_state.dataset_name}**")
    
    # Generate insights if not already done
    if st.session_state.insights is None:
        if st.button("🧠 Generate AI-Powered Insights", type="primary"):
            with st.spinner("Generating comprehensive business insights... This may take up to 30 seconds."):
                try:
                    config = get_config()
                    
                    # Generate insights
                    engine = InsightEngine(st.session_state.profile_results, config.all)
                    
                    # Prepare visualization summaries
                    viz_summaries = []
                    for fig, spec in st.session_state.visualizations:
                        viz_summaries.append(spec)
                    
                    insights = engine.generate_insights(viz_summaries)
                    
                    st.session_state.insights = insights
                    logger.info(f"Generated insights: {insights.get('word_count', 0)} words")
                    st.success("✅ Insights generated successfully!")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error generating insights: {str(e)}")
                    logger.error(f"Insights error: {str(e)}")
        else:
            st.info("👆 Click the button above to generate business insights powered by AI")
            st.markdown("""
            ### What will be generated?
            - Executive summary of key findings
            - Data-driven business insights
            - Risk and anomaly detection
            - Opportunity identification
            - Actionable recommendations
            - 800-1200 words of detailed analysis
            """)
        return
    
    # Display insights
    insights = st.session_state.insights
    
    # Show metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Word Count", insights.get('word_count', 'N/A'))
    with col2:
        st.metric("Model", insights.get('model', 'N/A'))
    with col3:
        tokens = insights.get('tokens', {})
        st.metric("Tokens Used", tokens.get('total', 'N/A'))
    
    st.markdown("---")
    
    # Display insights content
    content = insights.get('content', 'No insights available')
    
    # Create tabs for different sections
    sections = insights.get('sections', {})
    
    if sections:
        # Create tabs for each section
        tab_names = list(sections.keys())
        tabs = st.tabs(tab_names)
        
        for tab, section_name in zip(tabs, tab_names):
            with tab:
                st.markdown(sections[section_name])
    else:
        # Display full content if sections not extracted
        st.markdown(content)
    
    st.markdown("---")
    
    # Download options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        st.download_button(
            label="📥 Download as Markdown",
            data=content,
            file_name=f"{st.session_state.dataset_name}_insights.md",
            mime="text/markdown"
        )
    
    with col3:
        st.download_button(
            label="📥 Download as Text",
            data=content,
            file_name=f"{st.session_state.dataset_name}_insights.txt",
            mime="text/plain"
        )
    
    # Regenerate option
    st.markdown("---")
    if st.button("🔄 Regenerate Insights"):
        st.session_state.insights = None
        st.rerun()
