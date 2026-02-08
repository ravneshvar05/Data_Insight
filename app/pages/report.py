"""
Report page for PDF report generation and download.
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.report.pdf_generator import PDFReportGenerator
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def show():
    """Display the report generation page."""
    st.header("📄 Generate Report")
    
    # Check if dataset is loaded
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a dataset first.")
        return
    
    # Check if profiling is done
    if st.session_state.profile_results is None:
        st.warning("⚠️ Please run data profiling first.")
        st.info("👉 Navigate to **Data Profiling** to analyze your dataset.")
        return
    
    st.markdown(f"Generate comprehensive PDF report for: **{st.session_state.dataset_name}**")
    
    # Report options
    st.subheader("📋 Report Contents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ✅ **Dataset Overview**
        - Rows and columns count
        - Memory usage
        - Column types
        
        ✅ **Data Profiling**
        - Numeric statistics
        - Categorical analysis
        - Data quality report
        """)
    
    with col2:
        st.markdown("""
        ✅ **Visualizations**
        - All generated charts
        - Business context for each
        
        ✅ **Business Insights**
        - Executive summary
        - Key findings
        - Recommendations
        """)
    
    st.markdown("---")
    
    # Check what's available
    has_visualizations = len(st.session_state.visualizations) > 0
    has_insights = st.session_state.insights is not None
    
    if not has_visualizations:
        st.warning("⚠️ No visualizations generated yet. The report will include profiling only.")
        st.info("👉 Navigate to **Visualizations** to generate charts.")
    
    if not has_insights:
        st.warning("⚠️ No insights generated yet. The report will be incomplete.")
        st.info("👉 Navigate to **Insights** to generate business insights.")
    
    st.markdown("---")
    
    # Generate report button
    if st.button("📄 Generate PDF Report", type="primary"):
        with st.spinner("Generating PDF report... This may take a moment."):
            try:
                config = get_config()
                generator = PDFReportGenerator(config.all)
                
                # Create temporary file for PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    output_path = Path(tmp_file.name)
                
                # Prepare visualizations
                visualizations = st.session_state.visualizations if has_visualizations else []
                
                # Prepare insights
                insights = st.session_state.insights if has_insights else {
                    'content': 'Insights not generated.',
                    'word_count': 0,
                    'model': 'N/A'
                }
                
                # Generate report
                pdf_path = generator.generate_report(
                    output_path=output_path,
                    dataset_name=st.session_state.dataset_name,
                    profile_results=st.session_state.profile_results,
                    visualizations=visualizations,
                    insights=insights
                )
                
                # Read PDF file
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                # Clean up temp file
                output_path.unlink()
                
                st.success("✅ Report generated successfully!")
                
                # Display download button
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{st.session_state.dataset_name.replace('.csv', '')}_report_{timestamp}.pdf"
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
                
                logger.info(f"PDF report generated: {filename}")
                
                # Success message
                st.success(f"Report generated successfully: {file_path}")
                st.info(f"✅ Report saved as: **{filename}**")
            
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
                logger.error(f"Report generation error: {str(e)}")
    
    # Instructions
    st.markdown("---")
    st.subheader("💡 Tips")
    st.markdown("""
    - For the most comprehensive report, complete all steps first:
      1. Upload Dataset
      2. Run Data Profiling
      3. Generate Visualizations
      4. Generate Insights
      5. Generate Report
    - The PDF report can be shared with stakeholders
    - All visualizations will be embedded as images
    - Insights will be formatted for readability
    """)
