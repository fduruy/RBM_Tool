"""
inputs.py - Module for reading and validating input files (CSV/Excel)

This module handles:
- Reading CSV or Excel files from the input directory
- Validating the required columns
- Returning a clean DataFrame for processing
"""

import pandas as pd
import os
import logging
from typing import Optional

# Configure logging for debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_input_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Read an input file (CSV or Excel) and return a pandas DataFrame.
    
    Args:
        file_path (str): Path to the input file
        
    Returns:
        Optional[pd.DataFrame]: DataFrame containing the data, or None if error
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Input file not found: {file_path}")
            return None
            
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            # CSV files can use different separators, try to detect
            df = pd.read_csv(file_path, sep=None, engine='python')
            logger.info(f"Successfully read CSV file: {file_path}")
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
            logger.info(f"Successfully read Excel file: {file_path}")
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return None
            
        return df
            
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None


def validate_dataframe(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Validate that the DataFrame contains all required columns.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        required_columns (list): List of column names that must be present
        
    Returns:
        bool: True if all required columns are present, False otherwise
    """
    try:
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            logger.error(f"Available columns: {list(df.columns)}")
            return False
            
        logger.info(f"Data validation successful. All required columns present: {required_columns}")
        return True
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        return False


def read_and_validate_input(input_dir: str = 'data/input/', filename: str = 'GT_Valo.csv') -> Optional[pd.DataFrame]:
    """
    Main function to read and validate the input file.
    
    This is the primary entry point for reading input data.
    
    Args:
        input_dir (str): Directory containing input files
        filename (str): Name of the input file
        
    Returns:
        Optional[pd.DataFrame]: Validated DataFrame ready for processing, or None if error
    """
    try:
        # Construct full file path
        file_path = os.path.join(input_dir, filename)
        
        # Define required columns based on the expected data structure
        required_columns = ['TranNum', 'InsNum', 'ExternalParty', 'MTM', 'CCY', 'Way']
        
        # Read the file
        logger.info(f"Reading input file from: {file_path}")
        df = read_input_file(file_path)
        
        if df is None:
            return None
            
        # Validate the data
        if not validate_dataframe(df, required_columns):
            return None
            
        # Clean column names (remove whitespace, standardize case)
        df.columns = df.columns.str.strip().str.replace(' ', '_')
        
        # Ensure required columns exist after cleaning
        for col in required_columns:
            cleaned_col = col.strip().replace(' ', '_')
            if cleaned_col not in df.columns:
                logger.error(f"Required column '{col}' not found after cleaning")
                return None
                
        logger.info(f"Successfully read and validated {len(df)} rows of data")
        logger.debug(f"Data preview:\n{df.head()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error in read_and_validate_input: {str(e)}")
        return None


# Example usage (for testing)
if __name__ == "__main__":
    # Test reading the sample file
    df = read_and_validate_input(input_dir='../data/samples/', filename='GT_Valo.csv')
    if df is not None:
        print("\n" + "="*50)
        print("SUCCESS: Input data loaded and validated")
        print("="*50)
        print(f"Shape: {df.shape}")
        print(f"\nFirst few rows:")
        print(df.head())
        print(f"\nColumn types:")
        print(df.dtypes)
