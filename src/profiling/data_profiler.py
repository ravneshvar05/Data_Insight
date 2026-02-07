"""
Data profiling module for comprehensive dataset analysis.
Performs statistical analysis WITHOUT using LLMs - pandas/numpy only.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from scipy import stats
from sklearn.preprocessing import LabelEncoder
import json
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataProfiler:
    """
    Comprehensive data profiler that analyzes datasets and generates
    statistical insights without using LLMs.
    """
    
    def __init__(self, df: pd.DataFrame, config: dict):
        """
        Initialize the data profiler.
        
        Args:
            df: Pandas DataFrame to profile
            config: Configuration dictionary from config.yaml
        """
        self.df = df.copy()
        self.config = config
        self.profile_results = {}
        
        # Extract profiling configuration
        profiling_config = config.get('profiling', {})
        self.id_patterns = profiling_config.get('id_column_patterns', ['id', 'index', 'key'])
        self.high_cardinality_threshold = profiling_config.get('high_cardinality_threshold', 0.95)
        self.correlation_threshold = profiling_config.get('correlation_threshold', 0.6)
        self.outlier_method = profiling_config.get('outlier_method', 'IQR')
        self.outlier_multiplier = profiling_config.get('outlier_multiplier', 1.5)
        self.high_missing_threshold = profiling_config.get('high_missing_threshold', 0.5)
        self.top_n_categories = profiling_config.get('top_categories_count', 10)
        
        logger.info(f"DataProfiler initialized for dataset with {len(df)} rows and {len(df.columns)} columns")
    
    def profile(self) -> Dict[str, Any]:
        """
        Run complete profiling analysis.
        
        Returns:
            Dictionary containing all profiling results
        """
        logger.info("Starting comprehensive data profiling...")
        
        # Step 1: Classify columns FIRST
        column_classification = self._classify_columns()
        
        # Step 2: Build profile results, passing classification to methods that need it
        self.profile_results = {
            'overview': self._get_overview(),
            'columns': column_classification,
            'numeric_stats': self._profile_all_numeric(column_classification),
            'categorical_stats': self._profile_all_categorical(column_classification),
            'datetime_stats': self._profile_all_datetime(column_classification),
            'correlations': self._compute_correlations(column_classification),
            'data_quality': self._check_data_quality()
        }
        
        logger.info("Data profiling completed successfully")
        return self.profile_results
    
    def _get_overview(self) -> Dict[str, Any]:
        """Get high-level dataset overview."""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / (1024 * 1024),
            'column_names': list(self.df.columns)
        }
    
    def _classify_columns(self) -> Dict[str, List[str]]:
        """
        Classify columns into types: numeric, categorical, datetime, boolean, id.
        
        Returns:
            Dictionary with column names grouped by type
        """
        classification = {
            'numeric': [],
            'categorical': [],
            'datetime': [],
            'boolean': [],
            'id': []
        }
        
        for col in self.df.columns:
            # Check if it's an ID column first
            if self._is_id_column(col):
                classification['id'].append(col)
                continue
            
            # Check data type
            dtype = self.df[col].dtype
            
            if pd.api.types.is_numeric_dtype(dtype):
                # Check if it's boolean (only 0/1 or True/False)
                unique_vals = self.df[col].dropna().unique()
                if len(unique_vals) <= 2 and set(unique_vals).issubset({0, 1, True, False}):
                    classification['boolean'].append(col)
                else:
                    classification['numeric'].append(col)
            
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                classification['datetime'].append(col)
            
            else:
                # Try to parse as datetime
                try:
                    pd.to_datetime(self.df[col].dropna().head(100), errors='raise')
                    classification['datetime'].append(col)
                except:
                    classification['categorical'].append(col)
        
        logger.info(f"Column classification: {', '.join([f'{k}={len(v)}' for k, v in classification.items()])}")
        return classification
    
    def _is_id_column(self, col: str) -> bool:
        """
        Determine if a column is an ID/index column.
        
        Args:
            col: Column name
            
        Returns:
            True if column appears to be an ID/index
        """
        # Check pattern matching
        col_lower = col.lower()
        for pattern in self.id_patterns:
            if pattern in col_lower:
                logger.debug(f"Column '{col}' identified as ID column (pattern match: {pattern})")
                return True
        
        # Check cardinality
        non_null_count = self.df[col].notna().sum()
        if non_null_count == 0:
            return False
        
        unique_ratio = self.df[col].nunique() / non_null_count
        
        if unique_ratio >= self.high_cardinality_threshold:
            logger.debug(f"Column '{col}' identified as ID column (high cardinality: {unique_ratio:.2%})")
            return True
        
        return False
    
    def _profile_all_numeric(self, column_classification: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """Profile all numeric columns."""
        columns = column_classification.get('numeric', [])
        results = {}
        
        for col in columns:
            results[col] = self._profile_numeric(col)
        
        return results
    
    def _profile_numeric(self, col: str) -> Dict[str, Any]:
        """
        Profile a single numeric column.
        
        Args:
            col: Column name
            
        Returns:
            Dictionary of statistics
        """
        series = self.df[col].dropna()
        
        if len(series) == 0:
            return {'error': 'No non-null values'}
        
        # Basic statistics
        stats_dict = {
            'count': int(series.count()),
            'missing': int(self.df[col].isna().sum()),
            'missing_pct': float(self.df[col].isna().sum() / len(self.df) * 100),
            'mean': float(series.mean()),
            'median': float(series.median()),
            'std': float(series.std()),
            'min': float(series.min()),
            'max': float(series.max()),
            'q25': float(series.quantile(0.25)),
            'q75': float(series.quantile(0.75)),
        }
        
        # Advanced statistics
        try:
            stats_dict['skewness'] = float(stats.skew(series))
            stats_dict['kurtosis'] = float(stats.kurtosis(series))
        except:
            stats_dict['skewness'] = None
            stats_dict['kurtosis'] = None
        
        # Outlier detection using IQR method
        if self.outlier_method == 'IQR':
            q1 = stats_dict['q25']
            q3 = stats_dict['q75']
            iqr = q3 - q1
            lower_bound = q1 - self.outlier_multiplier * iqr
            upper_bound = q3 + self.outlier_multiplier * iqr
            
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            stats_dict['outlier_count'] = int(len(outliers))
            stats_dict['outlier_pct'] = float(len(outliers) / len(series) * 100)
        
        return stats_dict
    
    def _profile_all_categorical(self, column_classification: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """Profile all categorical columns."""
        columns = column_classification.get('categorical', [])
        results = {}
        
        for col in columns:
            results[col] = self._profile_categorical(col)
        
        return results
    
    def _profile_categorical(self, col: str) -> Dict[str, Any]:
        """
        Profile a single categorical column.
        
        Args:
            col: Column name
            
        Returns:
            Dictionary of statistics
        """
        series = self.df[col]
        
        # Basic statistics
        stats_dict = {
            'count': int(series.notna().sum()),
            'missing': int(series.isna().sum()),
            'missing_pct': float(series.isna().sum() / len(self.df) * 100),
            'unique_count': int(series.nunique())
        }
        
        # Top categories
        value_counts = series.value_counts().head(self.top_n_categories)
        total = series.notna().sum()
        
        top_categories = []
        for value, count in value_counts.items():
            top_categories.append({
                'value': str(value),
                'count': int(count),
                'percentage': float(count / total * 100) if total > 0 else 0
            })
        
        stats_dict['top_categories'] = top_categories
        stats_dict['entropy'] = float(stats.entropy(value_counts)) if len(value_counts) > 0 else 0
        
        return stats_dict
    
    def _profile_all_datetime(self, column_classification: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """Profile all datetime columns."""
        columns = column_classification.get('datetime', [])
        results = {}
        
        for col in columns:
            results[col] = self._profile_datetime(col)
        
        return results
    
    def _profile_datetime(self, col: str) -> Dict[str, Any]:
        """
        Profile a single datetime column.
        
        Args:
            col: Column name
            
        Returns:
            Dictionary of statistics
        """
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.df[col]):
            series = pd.to_datetime(self.df[col], errors='coerce')
        else:
            series = self.df[col]
        
        series = series.dropna()
        
        if len(series) == 0:
            return {'error': 'No valid datetime values'}
        
        stats_dict = {
            'count': int(series.count()),
            'missing': int(self.df[col].isna().sum()),
            'missing_pct': float(self.df[col].isna().sum() / len(self.df) * 100),
            'min_date': str(series.min()),
            'max_date': str(series.max()),
            'range_days': int((series.max() - series.min()).days)
        }
        
        # Try to infer frequency
        try:
            if len(series) > 1:
                time_diffs = series.sort_values().diff().dropna()
                most_common_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else None
                if most_common_diff:
                    stats_dict['inferred_frequency'] = str(most_common_diff)
        except:
            stats_dict['inferred_frequency'] = 'Unknown'
        
        return stats_dict
    
    def _compute_correlations(self, column_classification: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Compute correlation matrix for numeric columns.
        
        Returns:
            Dictionary with correlation matrix and strong correlations
        """
        numeric_cols = column_classification.get('numeric', [])
        
        if len(numeric_cols) < 2:
            return {
                'matrix': {},
                'strong_correlations': []
            }
        
        # Compute correlation matrix
        corr_matrix = self.df[numeric_cols].corr()
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                col1 = numeric_cols[i]
                col2 = numeric_cols[j]
                corr_value = corr_matrix.loc[col1, col2]
                
                if abs(corr_value) >= self.correlation_threshold:
                    strong_correlations.append({
                        'column1': col1,
                        'column2': col2,
                        'correlation': float(corr_value),
                        'strength': 'positive' if corr_value > 0 else 'negative'
                    })
        
        # Sort by absolute correlation value
        strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations
        }
    
    def _check_data_quality(self) -> Dict[str, Any]:
        """
        Check data quality issues.
        
        Returns:
            Dictionary of quality metrics
        """
        quality_report = {
            'duplicate_rows': int(self.df.duplicated().sum()),
            'duplicate_rows_pct': float(self.df.duplicated().sum() / len(self.df) * 100),
            'constant_columns': [],
            'high_missing_columns': []
        }
        
        # Check for constant columns
        for col in self.df.columns:
            if self.df[col].nunique() <= 1:
                quality_report['constant_columns'].append(col)
        
        # Check for high missing columns
        for col in self.df.columns:
            missing_pct = self.df[col].isna().sum() / len(self.df)
            if missing_pct >= self.high_missing_threshold:
                quality_report['high_missing_columns'].append({
                    'column': col,
                    'missing_pct': float(missing_pct * 100)
                })
        
        return quality_report
    
    def to_json(self) -> str:
        """
        Export profiling results to JSON string for LLM consumption.
        
        Returns:
            JSON string
        """
        # Create a simplified version for LLM
        llm_data = {
            'overview': self.profile_results.get('overview', {}),
            'column_types': self.profile_results.get('columns', {}),
            'sample_statistics': {},
            'strong_correlations': self.profile_results.get('correlations', {}).get('strong_correlations', []),
            'data_quality': self.profile_results.get('data_quality', {})
        }
        
        # Add summary statistics for each numeric column (not ID columns)
        for col, stats in self.profile_results.get('numeric_stats', {}).items():
            llm_data['sample_statistics'][col] = {
                'type': 'numeric',
                'mean': stats.get('mean'),
                'median': stats.get('median'),
                'std': stats.get('std'),
                'min': stats.get('min'),
                'max': stats.get('max')
            }
        
        # Add summary for categorical columns
        for col, stats in self.profile_results.get('categorical_stats', {}).items():
            llm_data['sample_statistics'][col] = {
                'type': 'categorical',
                'unique_count': stats.get('unique_count'),
                'top_values': [cat['value'] for cat in stats.get('top_categories', [])[:3]]
            }
        
        return json.dumps(llm_data, indent=2)
    
    def to_streamlit_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Convert profiling results to Streamlit-friendly DataFrames.
        
        Returns:
            Dictionary of DataFrames for display
        """
        tables = {}
        
        # Overview table
        overview = self.profile_results.get('overview', {})
        tables['overview'] = pd.DataFrame([overview])
        
        # Column classification
        columns = self.profile_results.get('columns', {})
        col_data = []
        for col_type, col_list in columns.items():
            for col in col_list:
                col_data.append({'Column': col, 'Type': col_type})
        tables['columns'] = pd.DataFrame(col_data)
        
        # Numeric statistics
        numeric_stats = self.profile_results.get('numeric_stats', {})
        if numeric_stats:
            tables['numeric'] = pd.DataFrame(numeric_stats).T
        
        # Categorical statistics (simplified)
        categorical_stats = self.profile_results.get('categorical_stats', {})
        if categorical_stats:
            cat_data = []
            for col, stats in categorical_stats.items():
                cat_data.append({
                    'Column': col,
                    'Unique Count': stats.get('unique_count'),
                    'Missing %': f"{stats.get('missing_pct', 0):.1f}%",
                    'Top Value': stats.get('top_categories', [{}])[0].get('value', 'N/A')
                })
            tables['categorical'] = pd.DataFrame(cat_data)
        
        # Data quality
        quality = self.profile_results.get('data_quality', {})
        tables['quality'] = pd.DataFrame([{
            'Duplicate Rows': quality.get('duplicate_rows', 0),
            'Duplicate %': f"{quality.get('duplicate_rows_pct', 0):.1f}%",
            'Constant Columns': len(quality.get('constant_columns', [])),
            'High Missing Columns': len(quality.get('high_missing_columns', []))
        }])
        
        return tables
