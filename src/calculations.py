"""
calculations.py - Main calculations module for RBM_Tool

This module orchestrates the calculation workflow:
1. Process all trades (identify internal/external)
2. Create portfolio matcher
3. Perform matching and optimization

It imports from:
- trade_processing.py: Trade identification functions
- portfolio_matcher.py: Portfolio matching algorithm
"""

import pandas as pd
import logging
from typing import Dict

from trade_processing import identify_internal_trades, identify_external_trades
from portfolio_matcher import PortfolioMatcher

logger = logging.getLogger(__name__)


def process_all_trades(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Main function to process all trades and compute matching.
    
    This is the primary entry point for trade calculations.
    
    Args:
        data (Dict[str, pd.DataFrame]): Dictionary with keys 'gt_valo', 'rep_sensi', 'offsetting'
        
    Returns:
        Dict[str, pd.DataFrame]: Dictionary with result DataFrames:
            - 'internal_sub_portfolios'
            - 'matched_trades'
            - 'external_usage'
            - 'unmatched_sensitivities'
    """
    try:
        logger.info("Starting trade processing...")
        
        # Identify Internal and External trades
        internal_trades = identify_internal_trades(data['gt_valo'])
        external_trades = identify_external_trades(data['gt_valo'])
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Internal trades: {len(internal_trades)}")
        logger.info(f"  - External trades: {len(external_trades)}")
        
        # Create portfolio matcher and perform matching
        matcher = PortfolioMatcher(
            internal_trades=internal_trades,
            external_trades=external_trades,
            rep_sensi=data['rep_sensi'],
            offsetting=data['offsetting']
        )
        
        results = matcher.match_portfolios()
        
        return results
        
    except Exception as e:
        logger.error(f"Error in process_all_trades: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


# Example usage (for testing)
if __name__ == "__main__":
    from inputs import read_and_validate_input
    
    # Test with sample data
    data = read_and_validate_input(input_dir='../data/samples/')
    
    if data:
        print("\n" + "="*50)
        print("TESTING CALCULATIONS MODULE")
        print("="*50)
        
        results = process_all_trades(data)
        
        for name, df in results.items():
            print(f"\n{name}:")
            print(f"Shape: {df.shape}")
            print(df.head())
