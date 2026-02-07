"""
Main entry point for the Streamlit application.
Multi-page app for automated data insights.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import get_config
from src.utils.logger import Logger

# Page configuration
st.set_page_config(
    page_title="Automated Data Insight System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize configuration and logging
try:
    config = get_config()
    Logger.setup(config.get_section('logging'))
except Exception as e:
    st.error(f"Failed to initialize configuration: {str(e)}")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">📊 Automated Data Insight System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload, Profile, Visualize, and Gain Insights from Your Data</div>', unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'dataset_name' not in st.session_state:
    st.session_state.dataset_name = None
if 'profile_results' not in st.session_state:
    st.session_state.profile_results = None
if 'visualizations' not in st.session_state:
    st.session_state.visualizations = []
if 'insights' not in st.session_state:
    st.session_state.insights = None

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

# Create navigation buttons
page = st.sidebar.radio(
    "Select a page:",
    ["📁 Upload Dataset", "🔍 Data Profiling", "📈 Visualizations", "💡 Insights", "📄 Generate Report"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Display current dataset info
if st.session_state.df is not None:
    st.sidebar.success(f"✅ Dataset loaded: **{st.session_state.dataset_name}**")
    st.sidebar.info(f"Rows: {len(st.session_state.df):,} | Columns: {len(st.session_state.df.columns)}")
else:
    st.sidebar.warning("⚠️ No dataset loaded")

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This system performs deep data profiling, generates business-relevant visualizations, "
    "and produces high-quality insights using advanced LLMs."
)

# Import and display selected page
if page == "📁 Upload Dataset":
    from app.pages import upload
    upload.show()
elif page == "🔍 Data Profiling":
    from app.pages import profiling
    profiling.show()
elif page == "📈 Visualizations":
    from app.pages import visualizations
    visualizations.show()
elif page == "💡 Insights":
    from app.pages import insights
    insights.show()
elif page == "📄 Generate Report":
    from app.pages import report
    report.show()
