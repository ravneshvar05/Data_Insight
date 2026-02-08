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
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }

    /* -------------------------------------------------------------------------
       SIDEBAR STYLING - Enhanced with Variables
       ------------------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* Navigation Radio Buttons - Pill Style */
    [data-testid="stRadio"] > div {
        background-color: transparent;
        padding: 0;
    }
    
    /* Define the look of options */
    [data-testid="stRadio"] label {
        background-color: transparent;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.25rem;
        transition: all 0.2s ease-in-out;
        color: var(--text-color);
        border: 1px solid transparent;
        cursor: pointer;
        opacity: 0.8;
    }

    /* Hover State */
    [data-testid="stRadio"] label:hover {
        background-color: rgba(128, 128, 128, 0.1);
        opacity: 1;
    }

    /* Selected State */
    [data-testid="stRadio"] label[data-checked="true"] {
        background-color: var(--primary-color);
        color: #ffffff !important; /* Always white on primary color */
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* -------------------------------------------------------------------------
       MAIN CONTENT STYLING - Professional Layout
       ------------------------------------------------------------------------- */
    .stApp {
        background-color: var(--background-color);
    }

    /* Main Header */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        color: var(--text-color);
        text-align: left;
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
        letter-spacing: -0.025em;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: var(--text-color);
        opacity: 0.7;
        text-align: left;
        margin-bottom: 2rem;
        padding-left: 0.5rem;
        font-weight: 400;
    }
    
    /* Native Component Containers ("Cards") */
    /* Target common block containers to give them 'Card' look */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: var(--secondary-background-color); /* Use secondary bg for card feel */
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* However, ensure nested blocks don't double-pad */
    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"] {
        background-color: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.875rem;
        font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        color: var(--text-color);
        font-weight: 700;
        font-size: 1.5rem !important;
    }

    /* DataFrames */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.1s;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Secondary Button (Standard) */
    [data-testid="baseButton-secondary"] {
        background-color: transparent;
        border: 1px solid rgba(128, 128, 128, 0.4);
        color: var(--text-color);
    }
    [data-testid="baseButton-secondary"]:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color);
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    /* -------------------------------------------------------------------------
       HIDE STREAMLIT CHROME (The "App" Look)
       ------------------------------------------------------------------------- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDeployButton"] {display: none;}
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
