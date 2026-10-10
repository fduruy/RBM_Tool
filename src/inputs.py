"""
inputs.py - Module for reading and validating input files (CSV/Excel)

This module handles:
- Reading CSV or Excel files from the input directory
- Validating the required columns for each file type
- Checking consistency between GT_Valo, Rep_Sensi, and Offsetting files
- Returning clean DataFrames for processing
"""

import pandas as pd
import os
import logging
from typing import Dict, Optional, Tuple

# Configure logging for debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_csv_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Read a CSV file and return a pandas DataFrame.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        Optional[pd.DataFrame]: DataFrame containing the data, or None if error
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Read CSV file with semicolon separator
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        # Clean column names (remove whitespace)
        df.columns = df.columns.str.strip()
        
        logger.info(f"Successfully read CSV file: {file_path} with {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        return None


def read_excel_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Read an Excel file and return a pandas DataFrame.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        Optional[pd.DataFrame]: DataFrame containing the data, or None if error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        logger.info(f"Successfully read Excel file: {file_path} with {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {str(e)}")
        return None


def validate_gt_valo(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate GT_Valo DataFrame structure.
    
    Args:
        df (pd.DataFrame): GT_Valo DataFrame to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_columns = ['TranNum', 'InsNum', 'ExternalParty', 'PricingModel', 'MTM', 'CCY', 'Way']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"GT_Valo missing required columns: {missing_columns}"
        logger.error(error_msg)
        return False, error_msg
        
    # Check for duplicate TranNum
    duplicate_trannum = df['TranNum'].duplicated().any()
    if duplicate_trannum:
        error_msg = f"GT_Valo has duplicate TranNum values"
        logger.error(error_msg)
        return False, error_msg
        
    logger.info(f"GT_Valo validation successful: {len(df)} trades")
    return True, ""


def validate_rep_sensi(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate Rep_Sensi DataFrame structure.
    
    Args:
        df (pd.DataFrame): Rep_Sensi DataFrame to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_columns = ['TranNum', 'InsNum', 'Index', 'Tenor', 'Gpt_Id', 'Delta']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Rep_Sensi missing required columns: {missing_columns}"
        logger.error(error_msg)
        return False, error_msg
        
    logger.info(f"Rep_Sensi validation successful: {len(df)} sensitivity records")
    return True, ""


def validate_offsetting(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate Offsetting DataFrame structure.
    
    Args:
        df (pd.DataFrame): Offsetting DataFrame to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    required_columns = ['TranNum', 'InsNum', 'Daily_PL', 'YTD_PNL', 'CCY']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Offsetting missing required columns: {missing_columns}"
        logger.error(error_msg)
        return False, error_msg
        
    # Check for duplicate TranNum
    duplicate_trannum = df['TranNum'].duplicated().any()
    if duplicate_trannum:
        error_msg = f"Offsetting has duplicate TranNum values"
        logger.error(error_msg)
        return False, error_msg
        
    logger.info(f"Offsetting validation successful: {len(df)} PnL records")
    return True, ""


def check_consistency(gt_valo_df: pd.DataFrame, rep_sensi_df: pd.DataFrame, 
                      offsetting_df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Check consistency between GT_Valo, Rep_Sensi, and Offsetting files.
    Each trade in GT_Valo must have:
    - At least one corresponding sensitivity in Rep_Sensi
    - A corresponding PnL record in Offsetting
    
    Args:
        gt_valo_df (pd.DataFrame): GT_Valo DataFrame
        rep_sensi_df (pd.DataFrame): Rep_Sensi DataFrame
        offsetting_df (pd.DataFrame): Offsetting DataFrame
        
    Returns:
        Tuple[bool, str]: (is_consistent, error_message)
    """
    try:
        # Get all TranNum from GT_Valo
        gt_trannums = set(gt_valo_df['TranNum'].unique())
        
        # Get TranNum from Rep_Sensi
        rep_trannums = set(rep_sensi_df['TranNum'].unique())
        
        # Get TranNum from Offsetting
        offset_trannums = set(offsetting_df['TranNum'].unique())
        
        # Find trades in GT_Valo without sensitivities
        missing_sensi = gt_trannums - rep_trannums
        if missing_sensi:
            error_msg = f"Trades without sensitivities: {sorted(missing_sensi)}"
            logger.error(error_msg)
            return False, error_msg
            
        # Find trades in GT_Valo without PnL
        missing_pnl = gt_trannums - offset_trannums
        if missing_pnl:
            error_msg = f"Trades without PnL data: {sorted(missing_pnl)}"
            logger.error(error_msg)
            return False, error_msg
            
        # Check that all Rep_Sensi TranNum exist in GT_Valo
        extra_sensi = rep_trannums - gt_trannums
        if extra_sensi:
            logger.warning(f"Rep_Sensi has trades not in GT_Valo: {sorted(extra_sensi)}")
            
        # Check that all Offsetting TranNum exist in GT_Valo
        extra_pnl = offset_trannums - gt_trannums
        if extra_pnl:
            logger.warning(f"Offsetting has trades not in GT_Valo: {sorted(extra_pnl)}")
            
        logger.info("Consistency check passed: all GT_Valo trades have sensitivities and PnL data")
        return True, ""
        
    except Exception as e:
        error_msg = f"Error during consistency check: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def read_and_validate_input(input_dir: str = 'data/input/') -> Optional[Dict[str, pd.DataFrame]]:
    """
    Main function to read and validate all input files.
    
    This is the primary entry point for reading input data.
    
    Args:
        input_dir (str): Directory containing input files
        
    Returns:
        Optional[Dict[str, pd.DataFrame]]: Dictionary with keys 'gt_valo', 'rep_sensi', 'offsetting'
    """
    try:
        logger.info(f"Reading input files from: {input_dir}")
        
        # Define file paths
        gt_valo_path = os.path.join(input_dir, 'GT_Valo.csv')
        rep_sensi_path = os.path.join(input_dir, 'Rep_Sensi.csv')
        offsetting_path = os.path.join(input_dir, 'Offsetting.csv')
        
        # Read all files
        gt_valo_df = read_csv_file(gt_valo_path)
        if gt_valo_df is None:
            # Try with samples directory
            samples_dir = os.path.join(os.path.dirname(input_dir), 'samples')
            gt_valo_path = os.path.join(samples_dir, 'GT_Valo.csv')
            rep_sensi_path = os.path.join(samples_dir, 'Rep_Sensi.csv')
            offsetting_path = os.path.join(samples_dir, 'Offsetting.csv')
            
            gt_valo_df = read_csv_file(gt_valo_path)
            rep_sensi_df = read_csv_file(rep_sensi_path)
            offsetting_df = read_csv_file(offsetting_path)
        else:
            rep_sensi_df = read_csv_file(rep_sensi_path)
            offsetting_df = read_csv_file(offsetting_path)
        
        if gt_valo_df is None or rep_sensi_df is None or offsetting_df is None:
            logger.error("One or more input files could not be read")
            return None
            
        # Validate each file
        gt_valid, gt_error = validate_gt_valo(gt_valo_df)
        rep_valid, rep_error = validate_rep_sensi(rep_sensi_df)
        offset_valid, offset_error = validate_offsetting(offsetting_df)
        
        if not (gt_valid and rep_valid and offset_valid):
            logger.error("One or more files failed validation")
            return None
            
        # Check consistency
        consistent, consistency_error = check_consistency(gt_valo_df, rep_sensi_df, offsetting_df)
        if not consistent:
            logger.error(f"Consistency check failed: {consistency_error}")
            return None
            
        logger.info("All input files read and validated successfully")
        logger.info(f"  - GT_Valo: {len(gt_valo_df)} trades")
        logger.info(f"  - Rep_Sensi: {len(rep_sensi_df)} sensitivity records")
        logger.info(f"  - Offsetting: {len(offsetting_df)} PnL records")
        
        return {
            'gt_valo': gt_valo_df,
            'rep_sensi': rep_sensi_df,
            'offsetting': offsetting_df
        }
        
    except Exception as e:
        logger.error(f"Error in read_and_validate_input: {str(e)}")
        return None


# Example usage (for testing)
if __name__ == "__main__":
    # Test reading the sample files
    data = read_and_validate_input(input_dir='../data/samples/')
    if data:
        print("\n" + "="*50)
        print("SUCCESS: All input data loaded and validated")
        print("="*50)
        print(f"GT_Valo shape: {data['gt_valo'].shape}")
        print(f"Rep_Sensi shape: {data['rep_sensi'].shape}")
        print(f"Offsetting shape: {data['offsetting'].shape}")
        print(f"\nGT_Valo columns: {list(data['gt_valo'].columns)}")
        print(f"Rep_Sensi columns: {list(data['rep_sensi'].columns)}")
        print(f"Offsetting columns: {list(data['offsetting'].columns)}")
