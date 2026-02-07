"""
Validation utilities for the Automated Data Insight System.
Validates uploaded files and data integrity.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
import chardet
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Validator for uploaded datasets."""
    
    def __init__(self, config: dict):
        """
        Initialize validator with configuration.
        
        Args:
            config: Application configuration
        """
        self.max_file_size = config.get('app.max_file_size_mb', 100) * 1024 * 1024  # Convert to bytes
        self.supported_formats = config.get('app.supported_formats', ['csv'])
    
    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate an uploaded file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file_path.exists():
            return False, "File does not exist"
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > self.max_file_size:
            return False, f"File size exceeds maximum allowed size of {self.max_file_size / (1024 * 1024):.0f} MB"
        
        # Check file extension
        extension = file_path.suffix.lower().replace('.', '')
        if extension not in self.supported_formats:
            return False, f"Unsupported file format. Supported formats: {', '.join(self.supported_formats)}"
        
        logger.info(f"File validation passed: {file_path.name}")
        return True, None
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Validate a pandas DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if DataFrame is empty
        if df.empty:
            return False, "Dataset is empty"
        
        # Check minimum rows
        if len(df) < 2:
            return False, "Dataset must have at least 2 rows"
        
        # Check minimum columns
        if len(df.columns) < 1:
            return False, "Dataset must have at least 1 column"
        
        # Check for invalid column names
        invalid_cols = []
        for col in df.columns:
            if not isinstance(col, str) or col.strip() == '':
                invalid_cols.append(col)
        
        if invalid_cols:
            return False, f"Invalid column names found: {invalid_cols}. Column names must be non-empty strings."
        
        logger.info(f"DataFrame validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True, None
    
    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """
        Detect the encoding of a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding (e.g., 'utf-8', 'latin-1')
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            # Default to utf-8 if detection fails
            if encoding is None:
                encoding = 'utf-8'
            
            logger.info(f"Detected encoding: {encoding} (confidence: {result['confidence']:.2f})")
            return encoding
    
    @staticmethod
    def load_csv(file_path: Path, encoding: Optional[str] = None) -> pd.DataFrame:
        """
        Load a CSV file into a DataFrame with proper error handling.
        
        Args:
            file_path: Path to the CSV file
            encoding: File encoding (auto-detected if None)
            
        Returns:
            Pandas DataFrame
            
        Raises:
            ValueError: If file cannot be loaded
        """
        try:
            if encoding is None:
                encoding = DataValidator.detect_encoding(file_path)
            
            # Try loading with detected encoding
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"Successfully loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            logger.warning(f"Failed to load with {encoding}, trying latin-1")
            try:
                df = pd.read_csv(file_path, encoding='latin-1')
                logger.info(f"Successfully loaded CSV with latin-1 encoding")
                return df
            except Exception as e:
                raise ValueError(f"Failed to load CSV file: {str(e)}")
        
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file: {str(e)}")
        
        except Exception as e:
            raise ValueError(f"Unexpected error loading CSV: {str(e)}")
