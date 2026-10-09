"""
outputs.py - Module for generating output files

This module handles:
- Writing results to CSV files in the output directory
- Formatting the output as specified: Internal trades et MTM, External trades et MTM
- Creating timestamped output files
"""

import pandas as pd
import os
import logging
from datetime import datetime
from typing import Optional

# Configure logging for debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ensure_output_directory(output_dir: str = 'data/output/') -> bool:
    """
    Ensure the output directory exists, create if it doesn't.
    
    Args:
        output_dir (str): Path to the output directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory ensured: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"Error ensuring output directory: {str(e)}")
        return False


def generate_output_filename(prefix: str = 'resultats', output_dir: str = 'data/output/') -> str:
    """
    Generate a timestamped output filename.
    
    Format: resultats[YYYYMMDD].csv
    
    Args:
        prefix (str): Prefix for the filename (default: 'resultats')
        output_dir (str): Output directory path
        
    Returns:
        str: Full path to the output file
    """
    try:
        # Get current date in YYYYMMDD format
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{prefix}{date_str}.csv"
        full_path = os.path.join(output_dir, filename)
        
        logger.info(f"Generated output filename: {full_path}")
        return full_path
    except Exception as e:
        logger.error(f"Error generating output filename: {str(e)}")
        return os.path.join(output_dir, f"{prefix}_error.csv")


def format_summary_for_output(summary_df: pd.DataFrame) -> pd.DataFrame:
    """
    Format the summary DataFrame for output.
    
    Ensures proper column ordering and formatting.
    
    Args:
        summary_df (pd.DataFrame): Summary DataFrame from calculations
        
    Returns:
        pd.DataFrame: Formatted DataFrame ready for output
    """
    try:
        # Ensure required columns exist
        required_columns = ['Trade_Type', 'CCY', 'Way', 'Count', 'Total_MTM']
        
        # Add any missing columns with default values
        for col in required_columns:
            if col not in summary_df.columns:
                summary_df[col] = None
        
        # Reorder columns
        formatted_df = summary_df[required_columns].copy()
        
        # Format numeric columns
        if 'Count' in formatted_df.columns:
            formatted_df['Count'] = formatted_df['Count'].astype(int)
        if 'Total_MTM' in formatted_df.columns:
            formatted_df['Total_MTM'] = formatted_df['Total_MTM'].round(2)
        
        logger.debug(f"Formatted summary for output:\n{formatted_df}")
        return formatted_df
        
    except Exception as e:
        logger.error(f"Error formatting summary for output: {str(e)}")
        return pd.DataFrame()


def write_csv_output(df: pd.DataFrame, file_path: str) -> bool:
    """
    Write a DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame to write
        file_path (str): Path to the output CSV file
        
    Returns:
        bool: True if write was successful
    """
    try:
        # Ensure directory exists
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write to CSV
        df.to_csv(file_path, index=False, sep=';', encoding='utf-8')
        logger.info(f"Successfully wrote output to: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error writing CSV output to {file_path}: {str(e)}")
        return False


def write_results(internal_trades: pd.DataFrame, external_trades: pd.DataFrame, 
                  combined_summary: pd.DataFrame, output_dir: str = 'data/output/') -> bool:
    """
    Main function to write all results to output files.
    
    This is the primary entry point for writing output data.
    
    Args:
        internal_trades (pd.DataFrame): Internal trades DataFrame
        external_trades (pd.DataFrame): External trades DataFrame
        combined_summary (pd.DataFrame): Combined summary DataFrame
        output_dir (str): Output directory path
        
    Returns:
        bool: True if all outputs were written successfully
    """
    try:
        logger.info("Starting to write output files...")
        
        # Ensure output directory exists
        if not ensure_output_directory(output_dir):
            return False
        
        # Format the summary for output
        formatted_summary = format_summary_for_output(combined_summary)
        
        # Generate output filename
        output_file = generate_output_filename('resultats', output_dir)
        
        # Write the formatted summary to CSV
        success = write_csv_output(formatted_summary, output_file)
        
        if success:
            logger.info(f"Output successfully written to: {output_file}")
            logger.info(f"Output contains {len(formatted_summary)} summary rows")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in write_results: {str(e)}")
        return False


def write_detailed_outputs(internal_trades: pd.DataFrame, external_trades: pd.DataFrame,
                           combined_summary: pd.DataFrame, output_dir: str = 'data/output/') -> bool:
    """
    Write detailed outputs including individual trade files and summary.
    
    Args:
        internal_trades (pd.DataFrame): Internal trades DataFrame
        external_trades (pd.DataFrame): External trades DataFrame
        combined_summary (pd.DataFrame): Combined summary DataFrame
        output_dir (str): Output directory path
        
    Returns:
        bool: True if all outputs were written successfully
    """
    try:
        logger.info("Writing detailed output files...")
        
        # Ensure output directory exists
        if not ensure_output_directory(output_dir):
            return False
        
        # Generate date string for filenames
        date_str = datetime.now().strftime('%Y%m%d')
        
        # Write Internal trades
        internal_file = os.path.join(output_dir, f"internal_trades_{date_str}.csv")
        write_csv_output(internal_trades, internal_file)
        
        # Write External trades
        external_file = os.path.join(output_dir, f"external_trades_{date_str}.csv")
        write_csv_output(external_trades, external_file)
        
        # Write combined summary
        summary_file = os.path.join(output_dir, f"resultats_{date_str}.csv")
        formatted_summary = format_summary_for_output(combined_summary)
        write_csv_output(formatted_summary, summary_file)
        
        logger.info(f"Detailed outputs written:")
        logger.info(f"  - Internal trades: {internal_file}")
        logger.info(f"  - External trades: {external_file}")
        logger.info(f"  - Summary: {summary_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in write_detailed_outputs: {str(e)}")
        return False


# Example usage (for testing)
if __name__ == "__main__":
    # Create sample data for testing
    sample_summary = pd.DataFrame({
        'Trade_Type': ['Internal', 'Internal', 'External', 'External'],
        'CCY': ['EUR', 'GBP', 'EUR', 'GBP'],
        'Way': ['Pay', 'Rec', 'Pay', 'Rec'],
        'Count': [3, 2, 5, 4],
        'Total_MTM': [15000.0, 20000.0, 25000.0, 30000.0]
    })
    
    sample_internal = pd.DataFrame({
        'TranNum': [1, 2, 3],
        'InsNum': [101, 102, 103],
        'ExternalParty': ['CLFRFRPP', 'CLFXYZ', 'FSAABC'],
        'MTM': [1000.0, 2000.0, 3000.0],
        'CCY': ['EUR', 'EUR', 'GBP'],
        'Way': ['Pay', 'Pay', 'Rec']
    })
    
    sample_external = pd.DataFrame({
        'TranNum': [4, 5, 6, 7, 8],
        'InsNum': [104, 105, 106, 107, 108],
        'ExternalParty': ['Bank', 'Bank', 'Bank', 'Bank', 'Bank'],
        'MTM': [4000.0, 5000.0, 6000.0, 7000.0, 8000.0],
        'CCY': ['EUR', 'EUR', 'EUR', 'GBP', 'GBP'],
        'Way': ['Pay', 'Pay', 'Pay', 'Rec', 'Rec']
    })
    
    print("\n" + "="*50)
    print("TESTING OUTPUTS MODULE")
    print("="*50)
    
    # Test formatting
    formatted = format_summary_for_output(sample_summary)
    print(f"\nFormatted summary:\n{formatted}")
    
    # Test writing (to a test directory)
    test_dir = '../data/output_test/'
    success = write_results(sample_internal, sample_external, sample_summary, test_dir)
    print(f"\nWrite results test: {'SUCCESS' if success else 'FAILED'}")
    
    # Test detailed outputs
    success = write_detailed_outputs(sample_internal, sample_external, sample_summary, test_dir)
    print(f"Write detailed outputs test: {'SUCCESS' if success else 'FAILED'}")
