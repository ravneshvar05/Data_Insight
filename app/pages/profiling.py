"""
Profiling page for displaying dataset statistics and data quality.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.profiling.data_profiler import DataProfiler
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def show():
    """Display the profiling page."""
    st.header("🔍 Data Profiling")
    
    # Check if dataset is loaded
    if st.session_state.df is None:
        st.warning("⚠️ Please upload a dataset first.")
        st.info("👉 Navigate to **Upload Dataset** to get started.")
        return
    
    st.markdown(f"Analyzing: **{st.session_state.dataset_name}**")
    
    # Run profiling if not already done
    if st.session_state.profile_results is None:
        if st.button("🚀 Run Data Profiling", type="primary"):
            with st.spinner("Analyzing dataset... This may take a moment."):
                try:
                    config = get_config()
                    profiler = DataProfiler(st.session_state.df, config.all)
                    profile_results = profiler.profile()
                    st.session_state.profile_results = profile_results
                    logger.info("Data profiling completed")
                    st.success("✅ Profiling complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error during profiling: {str(e)}")
                    logger.error(f"Profiling error: {str(e)}")
        else:
            st.info("👆 Click the button above to start profiling")
        return
    
    # Display profiling results
    profile_results = st.session_state.profile_results
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔢 Numeric Stats",
        "📝 Categorical Stats",
        "🔗 Correlations",
        "⚠️ Data Quality"
    ])
    
    with tab1:
        show_overview(profile_results)
    
    with tab2:
        show_numeric_stats(profile_results)
    
    with tab3:
        show_categorical_stats(profile_results)
    
    with tab4:
        show_correlations(profile_results)
    
    with tab5:
        show_data_quality(profile_results)
    
    # Download profiling results
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col2:
        profiler = DataProfiler(st.session_state.df, get_config().all)
        profiler.profile_results = profile_results
        json_data = profiler.to_json()
        
        st.download_button(
            label="📥 Download Profile (JSON)",
            data=json_data,
            file_name=f"{st.session_state.dataset_name}_profile.json",
            mime="application/json"
        )


def show_overview(profile_results):
    """Display dataset overview."""
    st.subheader("Dataset Overview")
    
    overview = profile_results.get('overview', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", f"{overview.get('rows', 0):,}")
    with col2:
        st.metric("Total Columns", f"{overview.get('columns', 0):,}")
    with col3:
        st.metric("Memory Usage", f"{overview.get('memory_usage_mb', 0):.2f} MB")
    
    st.markdown("### Column Classification")
    columns = profile_results.get('columns', {})
    
    col_data = []
    for col_type, col_list in columns.items():
        col_data.append({
            'Type': col_type.capitalize(),
            'Count': len(col_list),
            'Columns': ', '.join(col_list[:5]) + ('...' if len(col_list) > 5 else '')
        })
    
    st.dataframe(pd.DataFrame(col_data), use_container_width=True)


def show_numeric_stats(profile_results):
    """Display numeric column statistics."""
    st.subheader("Numeric Column Statistics")
    
    numeric_stats = profile_results.get('numeric_stats', {})
    
    if not numeric_stats:
        st.info("No numeric columns found in the dataset.")
        return
    
    # Create DataFrame for display
    stats_df = pd.DataFrame(numeric_stats).T
    
    # Round values for display
    display_cols = ['mean', 'median', 'std', 'min', 'max', 'skewness', 'kurtosis']
    for col in display_cols:
        if col in stats_df.columns:
            stats_df[col] = stats_df[col].round(2)
    
    st.dataframe(stats_df, use_container_width=True)
    
    # Outlier summary
    st.markdown("### Outlier Detection")
    outlier_data = []
    for col, stats in numeric_stats.items():
        if stats.get('outlier_count', 0) > 0:
            outlier_data.append({
                'Column': col,
                'Outliers': stats['outlier_count'],
                'Percentage': f"{stats.get('outlier_pct', 0):.1f}%"
            })
    
    if outlier_data:
        st.dataframe(pd.DataFrame(outlier_data), use_container_width=True)
    else:
        st.success("✅ No outliers detected in numeric columns.")


def show_categorical_stats(profile_results):
    """Display categorical column statistics."""
    st.subheader("Categorical Column Statistics")
    
    categorical_stats = profile_results.get('categorical_stats', {})
    
    if not categorical_stats:
        st.info("No categorical columns found in the dataset.")
        return
    
    # Summary table
    summary_data = []
    for col, stats in categorical_stats.items():
        top_value = stats.get('top_categories', [{}])[0]
        summary_data.append({
            'Column': col,
            'Unique Values': stats.get('unique_count', 0),
            'Missing %': f"{stats.get('missing_pct', 0):.1f}%",
            'Top Value': top_value.get('value', 'N/A'),
            'Top Freq': f"{top_value.get('percentage', 0):.1f}%"
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    # Detailed view for selected column
    st.markdown("### Detailed View")
    selected_col = st.selectbox("Select a column:", list(categorical_stats.keys()))
    
    if selected_col:
        stats = categorical_stats[selected_col]
        top_cats = stats.get('top_categories', [])
        
        if top_cats:
            cat_df = pd.DataFrame(top_cats)
            st.dataframe(cat_df, use_container_width=True)


def show_correlations(profile_results):
    """Display correlation analysis."""
    st.subheader("Correlation Analysis")
    
    correlations = profile_results.get('correlations', {})
    strong_corrs = correlations.get('strong_correlations', [])
    
    if not strong_corrs:
        st.info("No strong correlations found (threshold: 0.6)")
        return
    
    # Display strong correlations table
    st.markdown("### Strong Correlations")
    corr_data = []
    for corr in strong_corrs:
        corr_data.append({
            'Column 1': corr['column1'],
            'Column 2': corr['column2'],
            'Correlation': f"{corr['correlation']:.3f}",
            'Type': corr['strength'].capitalize()
        })
    
    st.dataframe(pd.DataFrame(corr_data), use_container_width=True)
    
    # Correlation heatmap
    st.markdown("### Correlation Matrix Heatmap")
    corr_matrix = correlations.get('matrix', {})
    
    if corr_matrix:
        corr_df = pd.DataFrame(corr_matrix)
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_df.values,
            x=corr_df.columns,
            y=corr_df.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_df.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Correlation Matrix",
            height=600,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_data_quality(profile_results):
    """Display data quality issues."""
    st.subheader("Data Quality Report")
    
    quality = profile_results.get('data_quality', {})
    
    # Duplicates
    st.markdown("### Duplicate Rows")
    dup_count = quality.get('duplicate_rows', 0)
    dup_pct = quality.get('duplicate_rows_pct', 0)
    
    if dup_count > 0:
        st.warning(f"⚠️ Found {dup_count:,} duplicate rows ({dup_pct:.1f}%)")
    else:
        st.success("✅ No duplicate rows found")
    
    # Constant columns
    st.markdown("### Constant Columns")
    const_cols = quality.get('constant_columns', [])
    
    if const_cols:
        st.warning(f"⚠️ Found {len(const_cols)} constant columns: {', '.join(const_cols)}")
        st.info("💡 Consider removing these columns as they provide no variance.")
    else:
        st.success("✅ No constant columns found")
    
    # High missing columns
    st.markdown("### High Missing Value Columns")
    high_missing = quality.get('high_missing_columns', [])
    
    if high_missing:
        missing_df = pd.DataFrame(high_missing)
        st.warning(f"⚠️ Found {len(high_missing)} columns with >50% missing values:")
        st.dataframe(missing_df, use_container_width=True)
        st.info("💡 Consider imputation or removal of these columns.")
    else:
        st.success("✅ No columns with excessive missing values")
