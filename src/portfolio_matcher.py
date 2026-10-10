"""
portfolio_matcher.py - Portfolio matching and optimization algorithm

This module implements the core matching algorithm:
- Create Internal Sub-Portfolios grouped by CCY, PricingModel, and WAY
- SubPortfolios are aggregates of sensitivities (no individual trade notion)
- Sensitivity per SubPortfolio = Sum of deltas by (Index, Tenor) for the group
- Find best external trade matches to reduce SubPortfolio sensitivity
- Iterative matching process with usage tracking
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from models import SubPortfolio, TradeInfo, SensitivityRecord
from utils import parse_numeric_value

logger = logging.getLogger(__name__)


class PortfolioMatcher:
    """
    Main class for portfolio matching and optimization.
    Implements the iterative matching algorithm described in requirements.
    
    The algorithm:
    1. Creates Internal Sub-Portfolios grouped by CCY, PricingModel, WAY
    2. Each SubPortfolio contains aggregated sensitivities (sum by Index, Tenor)
    3. For each SubPortfolio, finds external trades that reduce sensitivity
    4. Matches iteratively, starting with highest Gpt_Id
    5. Tracks usage percentage for each external trade
    """
    
    def __init__(self, internal_trades: List[TradeInfo], external_trades: List[TradeInfo],
                 rep_sensi: pd.DataFrame, offsetting: pd.DataFrame):
        """
        Initialize the PortfolioMatcher.
        
        Args:
            internal_trades (List[TradeInfo]): List of internal trades
            external_trades (List[TradeInfo]): List of external trades
            rep_sensi (pd.DataFrame): Rep_Sensi DataFrame with sensitivity data
            offsetting (pd.DataFrame): Offsetting DataFrame with PnL data
        """
        self.internal_trades = internal_trades
        self.external_trades = external_trades
        self.rep_sensi = rep_sensi
        self.offsetting = offsetting
        self.sub_portfolios: Dict[str, SubPortfolio] = {}
        self.matched_results: List[Dict] = []
        self.external_usage: Dict[int, float] = {}  # TranNum -> usage percentage (0.0 to 1.0)
        
    def create_sub_portfolios(self) -> Dict[str, SubPortfolio]:
        """
        Create Internal Sub-Portfolios grouped by CCY, PricingModel, and WAY.
        Each sub-portfolio contains AGGREGATED sensitivities (sum by Index, Tenor).
        
        Returns:
            Dict[str, SubPortfolio]: Dictionary of sub-portfolios with key format "CCY_PricingModel_Way"
        """
        try:
            # Group internal trades by CCY, PricingModel, WAY
            groups = defaultdict(list)
            for trade in self.internal_trades:
                key = f"{trade.CCY}_{trade.PricingModel}_{trade.Way}"
                groups[key].append(trade)
            
            # Create sub-portfolios with AGGREGATED sensitivities
            for key, trades in groups.items():
                sub_port = SubPortfolio(Name=key, Trades=trades, Sensitivities=[])
                
                # Calculate total sensitivity per (Index, Tenor) for ALL trades in this sub-portfolio
                sensi_dict = defaultdict(float)
                for trade in trades:
                    trade_sensi = self.rep_sensi[self.rep_sensi['TranNum'] == trade.TranNum]
                    for _, row in trade_sensi.iterrows():
                        index = row['Index']
                        tenor = row['Tenor']
                        delta = parse_numeric_value(row['Delta'])
                        sensi_dict[(index, tenor)] += delta
                
                sub_port.TotalSensitivity = dict(sensi_dict)
                
                self.sub_portfolios[key] = sub_port
                logger.info(f"Created sub-portfolio: {key} with {len(trades)} trades and {len(sub_port.TotalSensitivity)} unique sensitivity pairs")
            
            return self.sub_portfolios
            
        except Exception as e:
            logger.error(f"Error creating sub-portfolios: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def get_external_trades_by_group(self, ccy: str, pricing_model: str) -> List[TradeInfo]:
        """
        Get external trades that match the given CCY and PricingModel.
        Used for finding potential matches for a sub-portfolio.
        
        Args:
            ccy (str): Currency
            pricing_model (str): Pricing Model
            
        Returns:
            List[TradeInfo]: List of matching external trades
        """
        matching_trades = []
        for trade in self.external_trades:
            if trade.CCY == ccy and trade.PricingModel == pricing_model:
                matching_trades.append(trade)
        return matching_trades
    
    def get_external_sensitivities(self, trade: TradeInfo) -> List[SensitivityRecord]:
        """
        Get sensitivity records for an external trade.
        
        Args:
            trade (TradeInfo): External trade
            
        Returns:
            List[SensitivityRecord]: Sensitivity records for this trade
        """
        trade_sensi = self.rep_sensi[self.rep_sensi['TranNum'] == trade.TranNum]
        sensitivities = []
        for _, row in trade_sensi.iterrows():
            sensi = SensitivityRecord(
                TranNum=row['TranNum'],
                InsNum=row['InsNum'],
                Index=row['Index'],
                Tenor=row['Tenor'],
                Gpt_Id=int(row['Gpt_Id']),
                Delta=parse_numeric_value(row['Delta'])
            )
            sensitivities.append(sensi)
        return sensitivities
    
    def calculate_sensitivity_reduction(self, sub_port: SubPortfolio, external_trade: TradeInfo,
                                       external_sensi: List[SensitivityRecord]) -> float:
        """
        Calculate how much sensitivity would be reduced by matching with an external trade.
        Only considers sensitivities with the same Index and Tenor, but opposite WAY.
        
        Args:
            sub_port (SubPortfolio): Internal sub-portfolio
            external_trade (TradeInfo): External trade to match with
            external_sensi (List[SensitivityRecord]): Sensitivities of the external trade
            
        Returns:
            float: Total sensitivity reduction score (higher is better)
        """
        reduction = 0.0
        
        # Create a dictionary of external sensitivities
        external_sensi_dict = defaultdict(float)
        for sensi in external_sensi:
            external_sensi_dict[(sensi.Index, sensi.Tenor)] += sensi.Delta
        
        # Extract WAY from sub-portfolio name (last part after second underscore)
        sub_port_way = sub_port.Name.split('_')[-1] if len(sub_port.Name.split('_')) >= 3 else None
        
        # Calculate reduction for matching sensitivities
        for (index, tenor), delta in sub_port.TotalSensitivity.items():
            if (index, tenor) in external_sensi_dict:
                # Check if WAY is opposite (Pay vs Rec)
                if sub_port_way and ((sub_port_way == 'Pay' and external_trade.Way == 'Rec') or \
                                   (sub_port_way == 'Rec' and external_trade.Way == 'Pay')):
                    # Opposite WAY means sensitivities can offset each other
                    # Reduction is the absolute value of what can be offset
                    reduction += abs(min(delta, external_sensi_dict[(index, tenor)]))
        
        return reduction
    
    def find_best_match(self, sub_port: SubPortfolio) -> Tuple[Optional[TradeInfo], float]:
        """
        Find the best external trade to match with a sub-portfolio.
        Uses the algorithm: start by finding the trade that reduces the maximum of overall sensitivity,
        starting by the highest GPT_ID and going backward.
        
        Args:
            sub_port (SubPortfolio): Internal sub-portfolio to match
            
        Returns:
            Tuple[Optional[TradeInfo], float]: (best_trade, reduction_score)
        """
        # Extract CCY and PricingModel from sub-portfolio name
        parts = sub_port.Name.split('_')
        if len(parts) < 3:
            return None, 0.0
        
        ccy = parts[0]
        pricing_model = parts[1]
        
        # Get matching external trades
        matching_trades = self.get_external_trades_by_group(ccy, pricing_model)
        
        if not matching_trades:
            logger.warning(f"No external trades found for sub-portfolio: {sub_port.Name}")
            return None, 0.0
        
        # Sort external trades by highest Gpt_Id (from Rep_Sensi) descending
        # We need to get the max Gpt_Id for each trade
        trade_gpt_ids = {}
        for trade in matching_trades:
            trade_sensi = self.rep_sensi[self.rep_sensi['TranNum'] == trade.TranNum]
            if not trade_sensi.empty:
                max_gpt_id = trade_sensi['Gpt_Id'].max()
                trade_gpt_ids[trade.TranNum] = max_gpt_id
            else:
                trade_gpt_ids[trade.TranNum] = 0
        
        # Sort by Gpt_Id descending
        sorted_trades = sorted(
            matching_trades,
            key=lambda t: trade_gpt_ids.get(t.TranNum, 0),
            reverse=True
        )
        
        # Find the trade with maximum sensitivity reduction
        best_trade = None
        best_reduction = 0.0
        best_sensi = []
        
        for trade in sorted_trades:
            # Skip if already fully used
            if self.external_usage.get(trade.TranNum, 0.0) >= 1.0:
                continue
                
            external_sensi = self.get_external_sensitivities(trade)
            reduction = self.calculate_sensitivity_reduction(sub_port, trade, external_sensi)
            
            if reduction > best_reduction:
                best_reduction = reduction
                best_trade = trade
                best_sensi = external_sensi
        
        return best_trade, best_reduction
    
    def match_portfolios(self) -> Dict[str, pd.DataFrame]:
        """
        Main matching algorithm.
        Iteratively matches external trades to internal sub-portfolios to reduce sensitivity.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary with result DataFrames
        """
        try:
            # Create sub-portfolios
            self.create_sub_portfolios()
            
            # Initialize external trade usage
            for trade in self.external_trades:
                self.external_usage[trade.TranNum] = 0.0
            
            # Iterate through sub-portfolios
            for sub_port_name, sub_port in self.sub_portfolios.items():
                logger.info(f"\nProcessing sub-portfolio: {sub_port_name}")
                logger.info(f"  Initial sensitivity pairs: {len(sub_port.TotalSensitivity)}")
                logger.info(f"  Initial total sensitivity: {sum(abs(d) for d in sub_port.TotalSensitivity.values()):.2f}")
                
                # Iterative matching
                iteration = 0
                while iteration < 100:  # Max iterations to prevent infinite loop
                    best_trade, reduction = self.find_best_match(sub_port)
                    
                    if best_trade is None or reduction <= 0:
                        logger.info(f"  No more matches found for {sub_port_name}")
                        break
                    
                    # Get external sensitivities
                    external_sensi = self.get_external_sensitivities(best_trade)
                    
                    # Calculate how much of the external trade to use
                    # For now, use full trade (100%)
                    usage = 1.0
                    
                    # Update usage
                    self.external_usage[best_trade.TranNum] = usage
                    
                    # Record the match
                    match_record = {
                        'SubPortfolio': sub_port_name,
                        'External_TranNum': best_trade.TranNum,
                        'External_Usage': usage,
                        'Reduction': reduction,
                        'Index_Tenor_Matches': []
                    }
                    
                    # Find which sensitivities were matched
                    external_sensi_dict = defaultdict(float)
                    for sensi in external_sensi:
                        external_sensi_dict[(sensi.Index, sensi.Tenor)] += sensi.Delta
                    
                    for (index, tenor), delta in sub_port.TotalSensitivity.items():
                        if (index, tenor) in external_sensi_dict:
                            match_record['Index_Tenor_Matches'].append({
                                'Index': index,
                                'Tenor': tenor,
                                'Internal_Delta': delta,
                                'External_Delta': external_sensi_dict[(index, tenor)]
                            })
                    
                    self.matched_results.append(match_record)
                    
                    # Update sub-portfolio sensitivities (reduce by matched amount)
                    for (index, tenor), delta in list(sub_port.TotalSensitivity.items()):
                        if (index, tenor) in external_sensi_dict:
                            # Reduce the sub-portfolio sensitivity by the external sensitivity
                            sub_port.TotalSensitivity[(index, tenor)] -= external_sensi_dict[(index, tenor)] * usage
                            # Remove if close to zero
                            if abs(sub_port.TotalSensitivity[(index, tenor)]) < 0.01:
                                del sub_port.TotalSensitivity[(index, tenor)]
                    
                    #logger.info(f"  Iteration {iteration + 1}: Matched with trade {best_trade.TranNum}, reduction: {reduction:.2f}")
                    #logger.info(f"  Remaining sensitivities: {len(sub_port.TotalSensitivity)}")
                    
                    iteration += 1
                
                # Record final state
                sub_port_result = {
                    'SubPortfolio': sub_port_name,
                    'Remaining_Sensitivities': [
                        {'Index': idx, 'Tenor': tenor, 'Delta': delta}
                        for (idx, tenor), delta in sub_port.TotalSensitivity.items()
                    ]
                }
                self.matched_results.append(sub_port_result)
            
            logger.info(f"\nMatching completed. Total matches: {len([r for r in self.matched_results if 'External_TranNum' in r])}")
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error in match_portfolios: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def get_results(self) -> Dict[str, pd.DataFrame]:
        """
        Get all results in a structured format.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary with keys:
                - 'internal_sub_portfolios' (NO TranNum column, only aggregated sensitivities)
                - 'matched_trades'
                - 'external_usage'
                - 'unmatched_sensitivities'
        """
        try:
            # Create Internal Sub-Portfolios table WITHOUT TranNum column
            # Only show aggregated sensitivities per SubPortfolio, Index, Tenor
            internal_sub_portfolios_data = []
            for sub_port_name, sub_port in self.sub_portfolios.items():
                for (index, tenor), delta in sub_port.TotalSensitivity.items():
                    internal_sub_portfolios_data.append({
                        'SubPortfolio': sub_port_name,
                        'Index': index,
                        'Tenor': tenor,
                        'Delta': delta
                    })
            
            internal_sub_portfolios_df = pd.DataFrame(internal_sub_portfolios_data)
            
            # Create Matched Trades table
            matched_trades_data = []
            for record in self.matched_results:
                if 'External_TranNum' in record:
                    matched_trades_data.append({
                        'SubPortfolio': record['SubPortfolio'],
                        'External_TranNum': record['External_TranNum'],
                        'External_Usage_Percentage': record['External_Usage'] * 100,
                        'Reduction': record['Reduction']
                    })
            
            matched_trades_df = pd.DataFrame(matched_trades_data)
            
            # Create External Usage table
            external_usage_data = []
            for trade in self.external_trades:
                usage = self.external_usage.get(trade.TranNum, 0.0)
                external_usage_data.append({
                    'TranNum': trade.TranNum,
                    'InsNum': trade.InsNum,
                    'ExternalParty': trade.ExternalParty,
                    'CCY': trade.CCY,
                    'PricingModel': trade.PricingModel,
                    'Way': trade.Way,
                    'Usage_Percentage': usage * 100
                })
            
            external_usage_df = pd.DataFrame(external_usage_data)
            
            # Create Unmatched Sensitivities table
            unmatched_data = []
            for sub_port_name, sub_port in self.sub_portfolios.items():
                for (index, tenor), delta in sub_port.TotalSensitivity.items():
                    unmatched_data.append({
                        'SubPortfolio': sub_port_name,
                        'Index': index,
                        'Tenor': tenor,
                        'Delta': delta
                    })
            
            unmatched_df = pd.DataFrame(unmatched_data)
            
            return {
                'internal_sub_portfolios': internal_sub_portfolios_df,
                'matched_trades': matched_trades_df,
                'external_usage': external_usage_df,
                'unmatched_sensitivities': unmatched_df
            }
            
        except Exception as e:
            logger.error(f"Error generating results: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
