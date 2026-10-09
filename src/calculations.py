"""
calculations.py - Module for processing and calculating trade data

This module handles:
- Identifying Internal trades (CLF* or FSA* in ExternalParty column)
- Identifying External trades (all others)
- Regrouping trades by CCY and WAY (e.g., EUR_Pay, GBP_Rec)
- Computing summaries of internal and external trades
"""

import pandas as pd
import logging
from typing import Tuple, Dict, Optional

# Configure logging for debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def identify_internal_trades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify Internal trades based on ExternalParty column.
    
    Internal trades are those where ExternalParty starts with 'CLF' or 'FSA'.
    
    Args:
        df (pd.DataFrame): Input DataFrame with trade data
        
    Returns:
        pd.DataFrame: DataFrame containing only Internal trades
    """
    try:
        # Check if ExternalParty column exists
        if 'ExternalParty' not in df.columns:
            logger.error("ExternalParty column not found in DataFrame")
            return pd.DataFrame()
            
        # Identify Internal trades (CLF* or FSA*)
        internal_mask = df['ExternalParty'].str.startswith(('CLF', 'FSA'), na=False)
        internal_trades = df[internal_mask].copy()
        
        logger.info(f"Found {len(internal_trades)} Internal trades out of {len(df)} total trades")
        logger.debug(f"Internal trades preview:\n{internal_trades.head()}")
        
        return internal_trades
        
    except Exception as e:
        logger.error(f"Error identifying Internal trades: {str(e)}")
        return pd.DataFrame()


def identify_external_trades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify External trades (all trades that are not Internal).
    
    Args:
        df (pd.DataFrame): Input DataFrame with trade data
        
    Returns:
        pd.DataFrame: DataFrame containing only External trades
    """
    try:
        # Check if ExternalParty column exists
        if 'ExternalParty' not in df.columns:
            logger.error("ExternalParty column not found in DataFrame")
            return pd.DataFrame()
            
        # Identify External trades (not CLF* or FSA*)
        external_mask = ~df['ExternalParty'].str.startswith(('CLF', 'FSA'), na=False)
        external_trades = df[external_mask].copy()
        
        logger.info(f"Found {len(external_trades)} External trades out of {len(df)} total trades")
        logger.debug(f"External trades preview:\n{external_trades.head()}")
        
        return external_trades
        
    except Exception as e:
        logger.error(f"Error identifying External trades: {str(e)}")
        return pd.DataFrame()


def group_trades_by_ccy_and_way(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Regroup trades by CCY and WAY combination.
    
    Creates groups like 'EUR_Pay', 'GBP_Rec', etc.
    
    Args:
        df (pd.DataFrame): Input DataFrame with trade data
        
    Returns:
        Dict[str, pd.DataFrame]: Dictionary with keys as CCY_WAY combinations
                               and values as corresponding DataFrames
    """
    try:
        # Check if required columns exist
        if 'CCY' not in df.columns or 'Way' not in df.columns:
            logger.error("CCY or Way column not found in DataFrame")
            return {}
            
        # Create CCY_WAY combination
        df['CCY_WAY'] = df['CCY'] + '_' + df['Way']
        
        # Group by CCY_WAY
        grouped = {}
        for ccy_way, group_df in df.groupby('CCY_WAY'):
            grouped[ccy_way] = group_df.copy()
            logger.info(f"Group {ccy_way}: {len(group_df)} trades")
            
        logger.info(f"Created {len(grouped)} groups based on CCY and WAY")
        return grouped
        
    except Exception as e:
        logger.error(f"Error grouping trades by CCY and WAY: {str(e)}")
        return {}


def compute_trade_summary(df: pd.DataFrame, trade_type: str = "Trade") -> pd.DataFrame:
    """
    Compute a summary of trades with total MTM by CCY and WAY.
    
    Args:
        df (pd.DataFrame): Input DataFrame with trade data
        trade_type (str): Type of trade (e.g., 'Internal', 'External')
        
    Returns:
        pd.DataFrame: Summary DataFrame with CCY, WAY, Count, and Total MTM
    """
    try:
        # Check if required columns exist
        if 'CCY' not in df.columns or 'Way' not in df.columns or 'MTM' not in df.columns:
            logger.error("Required columns (CCY, Way, MTM) not found in DataFrame")
            return pd.DataFrame()
            
        # Convert MTM to numeric (in case it was read as string)
        df['MTM'] = pd.to_numeric(df['MTM'], errors='coerce')
        
        # Group by CCY and Way, then aggregate
        summary = df.groupby(['CCY', 'Way']).agg(
            Count=('MTM', 'count'),
            Total_MTM=('MTM', 'sum')
        ).reset_index()
        
        # Add trade type column
        summary['Trade_Type'] = trade_type
        
        # Reorder columns for better readability
        summary = summary[['Trade_Type', 'CCY', 'Way', 'Count', 'Total_MTM']]
        
        logger.info(f"Computed summary for {trade_type} trades: {len(summary)} unique combinations")
        logger.debug(f"{trade_type} trades summary:\n{summary}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error computing {trade_type} trades summary: {str(e)}")
        return pd.DataFrame()


def process_all_trades(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main function to process all trades and compute summaries.
    
    This is the primary entry point for trade calculations.
    
    Args:
        df (pd.DataFrame): Input DataFrame with all trade data
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - Internal trades DataFrame
            - External trades DataFrame  
            - Combined summary DataFrame
    """
    try:
        logger.info("Starting trade processing...")
        
        # Identify Internal and External trades
        internal_trades = identify_internal_trades(df)
        external_trades = identify_external_trades(df)
        
        # Compute summaries
        internal_summary = compute_trade_summary(internal_trades, 'Internal')
        external_summary = compute_trade_summary(external_trades, 'External')
        
        # Combine summaries
        combined_summary = pd.concat([internal_summary, external_summary], ignore_index=True)
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Internal trades: {len(internal_trades)}")
        logger.info(f"  - External trades: {len(external_trades)}")
        logger.info(f"  - Total trades: {len(df)}")
        
        return internal_trades, external_trades, combined_summary
        
    except Exception as e:
        logger.error(f"Error in process_all_trades: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# Example usage (for testing)
if __name__ == "__main__":
    # Create sample data for testing
    sample_data = {
        'TranNum': [1, 2, 3, 4, 5],
        'InsNum': [101, 102, 103, 104, 105],
        'ExternalParty': ['CLFRFRPP', 'Bank', 'FSAABC', 'CLFXYZ', 'Bank'],
        'MTM': [1000.0, 2000.0, 1500.0, 3000.0, 2500.0],
        'CCY': ['EUR', 'EUR', 'GBP', 'GBP', 'EUR'],
        'Way': ['Pay', 'Pay', 'Rec', 'Rec', 'Pay']
    }
    
    sample_df = pd.DataFrame(sample_data)
    
    print("\n" + "="*50)
    print("TESTING CALCULATIONS MODULE")
    print("="*50)
    
    # Test each function
    internal = identify_internal_trades(sample_df)
    external = identify_external_trades(sample_df)
    grouped = group_trades_by_ccy_and_way(sample_df)
    internal_summary = compute_trade_summary(internal, 'Internal')
    external_summary = compute_trade_summary(external, 'External')
    
    print(f"\nInternal trades:\n{internal}")
    print(f"\nExternal trades:\n{external}")
    print(f"\nGrouped trades: {list(grouped.keys())}")
    print(f"\nInternal summary:\n{internal_summary}")
    print(f"\nExternal summary:\n{external_summary}")
    
    # Test main processing function
    print("\n" + "="*50)
    print("TESTING MAIN PROCESSING FUNCTION")
    print("="*50)
    internal_trades, external_trades, combined_summary = process_all_trades(sample_df)
    print(f"\nCombined summary:\n{combined_summary}")
