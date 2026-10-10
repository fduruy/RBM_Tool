"""
outputs.py - Module for generating output files

This module handles:
- Writing results to CSV files in the output directory
- Generating detailed tables for:
  - Internal Sub-Portfolios with sensitivities
  - Matched trades between internal and external
  - External trade usage percentages
  - Unmatched sensitivities
- Creating timestamped output files
"""

import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict, Optional

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
    
    Format: prefix_YYYYMMDD_HHMMSS.csv
    
    Args:
        prefix (str): Prefix for the filename (default: 'resultats')
        output_dir (str): Output directory path
        
    Returns:
        str: Full path to the output file
    """
    try:
        # Get current date and time in YYYYMMDD_HHMMSS format
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{date_str}.csv"
        full_path = os.path.join(output_dir, filename)
        
        logger.info(f"Generated output filename: {full_path}")
        return full_path
    except Exception as e:
        logger.error(f"Error generating output filename: {str(e)}")
        return os.path.join(output_dir, f"{prefix}_error.csv")


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
        
        # Write to CSV with semicolon separator
        df.to_csv(file_path, index=False, sep=';', encoding='utf-8', decimal=',')
        logger.info(f"Successfully wrote output to: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error writing CSV output to {file_path}: {str(e)}")
        return False


def format_dataframe_for_output(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """
    Format a DataFrame for output with proper column ordering and formatting.
    
    Args:
        df (pd.DataFrame): DataFrame to format
        filename (str): Name of the output file (for logging)
        
    Returns:
        pd.DataFrame: Formatted DataFrame ready for output
    """
    try:
        if df.empty:
            logger.warning(f"DataFrame for {filename} is empty")
            return df
        
        # Format numeric columns
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32']:
                df[col] = df[col].round(2)
            elif df[col].dtype in ['int64', 'int32']:
                df[col] = df[col].astype(int)
        
        logger.debug(f"Formatted DataFrame for {filename}:\n{df.head()}")
        return df
        
    except Exception as e:
        logger.error(f"Error formatting DataFrame for {filename}: {str(e)}")
        return pd.DataFrame()


def write_results(results: Dict[str, pd.DataFrame], output_dir: str = 'data/output/') -> bool:
    """
    Main function to write all results to output files.
    
    This is the primary entry point for writing output data.
    Generates separate files for each result type.
    
    Args:
        results (Dict[str, pd.DataFrame]): Dictionary with result DataFrames
        output_dir (str): Output directory path
        
    Returns:
        bool: True if all outputs were written successfully
    """
    try:
        logger.info("Starting to write output files...")
        
        # Ensure output directory exists
        if not ensure_output_directory(output_dir):
            return False
        
        # Define output files
        output_files = {
            'internal_sub_portfolios': 'Internal_SubPortfolios',
            'matched_trades': 'Matched_Trades',
            'external_usage': 'External_Usage',
            'unmatched_sensitivities': 'Unmatched_Sensitivities'
        }
        
        # Write each result to a separate file
        written_files = []
        for key, prefix in output_files.items():
            if key in results and not results[key].empty:
                formatted_df = format_dataframe_for_output(results[key], prefix)
                output_file = generate_output_filename(prefix, output_dir)
                success = write_csv_output(formatted_df, output_file)
                if success:
                    written_files.append(output_file)
                    logger.info(f"Wrote {prefix}: {output_file}")
            else:
                logger.warning(f"No data for {key}, skipping")
        
        if written_files:
            logger.info(f"\nSuccessfully wrote {len(written_files)} output files:")
            for f in written_files:
                logger.info(f"  - {f}")
        
        return len(written_files) > 0
        
    except Exception as e:
        logger.error(f"Error in write_results: {str(e)}")
        return False


def write_summary_report(results: Dict[str, pd.DataFrame], output_dir: str = 'data/output/') -> bool:
    """
    Write a comprehensive summary report combining all results.
    
    Args:
        results (Dict[str, pd.DataFrame]): Dictionary with result DataFrames
        output_dir (str): Output directory path
        
    Returns:
        bool: True if summary was written successfully
    """
    try:
        logger.info("Writing summary report...")
        
        # Ensure output directory exists
        if not ensure_output_directory(output_dir):
            return False
        
        # Create summary DataFrame
        summary_data = []
        
        # Internal Sub-Portfolios summary
        if 'internal_sub_portfolios' in results and not results['internal_sub_portfolios'].empty:
            internal_df = results['internal_sub_portfolios']
            for sub_port in internal_df['SubPortfolio'].unique():
                sub_port_df = internal_df[internal_df['SubPortfolio'] == sub_port]
                total_delta = sub_port_df['Delta'].sum()
                used_pct = sub_port_df['Used_Percentage'].mean()
                
                summary_data.append({
                    'Category': 'Internal Sub-Portfolios',
                    'Name': sub_port,
                    'Count': len(sub_port_df),
                    'Total_Delta': total_delta,
                    'Avg_Usage_Pct': used_pct
                })
        
        # Matched Trades summary
        if 'matched_trades' in results and not results['matched_trades'].empty:
            matched_df = results['matched_trades']
            for _, row in matched_df.iterrows():
                summary_data.append({
                    'Category': 'Matched Trades',
                    'Name': row['SubPortfolio'],
                    'Internal_TranNums': row['Internal_TranNums'],
                    'External_TranNum': row['External_TranNum'],
                    'Usage_Pct': row['External_Usage_Percentage'],
                    'Reduction': row['Reduction']
                })
        
        # External Usage summary
        if 'external_usage' in results and not results['external_usage'].empty:
            external_df = results['external_usage']
            for _, row in external_df.iterrows():
                summary_data.append({
                    'Category': 'External Usage',
                    'TranNum': row['TranNum'],
                    'ExternalParty': row['ExternalParty'],
                    'CCY': row['CCY'],
                    'PricingModel': row['PricingModel'],
                    'Usage_Pct': row['Usage_Percentage']
                })
        
        # Unmatched Sensitivities summary
        if 'unmatched_sensitivities' in results and not results['unmatched_sensitivities'].empty:
            unmatched_df = results['unmatched_sensitivities']
            for _, row in unmatched_df.iterrows():
                summary_data.append({
                    'Category': 'Unmatched Sensitivities',
                    'SubPortfolio': row['SubPortfolio'],
                    'Index': row['Index'],
                    'Tenor': row['Tenor'],
                    'Delta': row['Delta']
                })
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_data)
        
        # Write summary to file
        output_file = generate_output_filename('Summary_Report', output_dir)
        formatted_df = format_dataframe_for_output(summary_df, 'Summary_Report')
        success = write_csv_output(formatted_df, output_file)
        
        if success:
            logger.info(f"Summary report written to: {output_file}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error writing summary report: {str(e)}")
        return False


def write_all_outputs(results: Dict[str, pd.DataFrame], output_dir: str = 'data/output/') -> bool:
    """
    Write all outputs including detailed files and summary report.
    
    Args:
        results (Dict[str, pd.DataFrame]): Dictionary with result DataFrames
        output_dir (str): Output directory path
        
    Returns:
        bool: True if all outputs were written successfully
    """
    try:
        logger.info("Writing all output files...")
        
        # Write detailed results
        detailed_success = write_results(results, output_dir)
        
        # Write summary report
        summary_success = write_summary_report(results, output_dir)
        
        return detailed_success and summary_success
        
    except Exception as e:
        logger.error(f"Error in write_all_outputs: {str(e)}")
        return False


# Example usage (for testing)
if __name__ == "__main__":
    from calculations import process_all_trades
    from inputs import read_and_validate_input
    
    # Test with sample data
    data = read_and_validate_input(input_dir='../data/samples/')
    
    if data:
        results = process_all_trades(data)
        
        print("\n" + "="*50)
        print("TESTING OUTPUTS MODULE")
        print("="*50)
        
        # Test writing
        success = write_all_outputs(results, output_dir='../data/output_test/')
        print(f"\nWrite all outputs test: {'SUCCESS' if success else 'FAILED'}")
