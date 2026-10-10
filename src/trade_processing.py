"""
trade_processing.py - Trade identification and processing functions

This module handles:
- Identifying Internal trades (CLF* or FSA* in ExternalParty column)
- Identifying External trades (all others)
- Converting DataFrames to TradeInfo objects
"""

import pandas as pd
import logging
from typing import List

from models import TradeInfo
from utils import parse_numeric_value

logger = logging.getLogger(__name__)


def identify_internal_trades(df: pd.DataFrame) -> List[TradeInfo]:
    """
    Identify Internal trades based on ExternalParty column.
    Internal trades are those where ExternalParty starts with 'CLF' or 'FSA'.
    
    Args:
        df (pd.DataFrame): GT_Valo DataFrame
        
    Returns:
        List[TradeInfo]: List of Internal TradeInfo objects
    """
    try:
        internal_mask = df['ExternalParty'].str.startswith(('CLF', 'FSA'), na=False)
        internal_df = df[internal_mask].copy()
        
        trades = []
        for _, row in internal_df.iterrows():
            trade = TradeInfo(
                TranNum=int(row['TranNum']),
                InsNum=int(row['InsNum']),
                ExternalParty=str(row['ExternalParty']),
                PricingModel=str(row['PricingModel']),
                MTM=parse_numeric_value(row['MTM']),
                CCY=str(row['CCY']),
                Way=str(row['Way']),
                IsInternal=True
            )
            trades.append(trade)
        
        logger.info(f"Found {len(trades)} Internal trades")
        return trades
        
    except Exception as e:
        logger.error(f"Error identifying Internal trades: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def identify_external_trades(df: pd.DataFrame) -> List[TradeInfo]:
    """
    Identify External trades (all trades that are not Internal).
    
    Args:
        df (pd.DataFrame): GT_Valo DataFrame
        
    Returns:
        List[TradeInfo]: List of External TradeInfo objects
    """
    try:
        external_mask = ~df['ExternalParty'].str.startswith(('CLF', 'FSA'), na=False)
        external_df = df[external_mask].copy()
        
        trades = []
        for _, row in external_df.iterrows():
            trade = TradeInfo(
                TranNum=int(row['TranNum']),
                InsNum=int(row['InsNum']),
                ExternalParty=str(row['ExternalParty']),
                PricingModel=str(row['PricingModel']),
                MTM=parse_numeric_value(row['MTM']),
                CCY=str(row['CCY']),
                Way=str(row['Way']),
                IsInternal=False
            )
            trades.append(trade)
        
        logger.info(f"Found {len(trades)} External trades")
        return trades
        
    except Exception as e:
        logger.error(f"Error identifying External trades: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []
