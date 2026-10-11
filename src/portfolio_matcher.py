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
        
        # Pre-compute and cache external trade sensitivities for performance
        self.external_sensitivities_cache: Dict[int, List[SensitivityRecord]] = {}
        self.external_max_gpt_id: Dict[int, int] = {}
        self._precompute_external_cache()
        
        # Pre-sort external trades by max Gpt_Id descending for efficient iteration
        self.sorted_external_trades: List[TradeInfo] = []
        self._sort_external_trades()
        
    def _precompute_external_cache(self) -> None:
        """
        Pre-compute and cache external trade sensitivities and max Gpt_Id for performance.
        This avoids repeated DataFrame lookups during matching.
        """
        try:
            for trade in self.external_trades:
                trade_sensi = self.rep_sensi[self.rep_sensi['TranNum'] == trade.TranNum]
                sensitivities = []
                max_gpt_id = 0
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
                    if int(row['Gpt_Id']) > max_gpt_id:
                        max_gpt_id = int(row['Gpt_Id'])
                self.external_sensitivities_cache[trade.TranNum] = sensitivities
                self.external_max_gpt_id[trade.TranNum] = max_gpt_id
        except Exception as e:
            logger.error(f"Error precomputing external cache: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    def _sort_external_trades(self) -> None:
        """
        Pre-sort external trades by max Gpt_Id descending for efficient iteration.
        """
        try:
            self.sorted_external_trades = sorted(
                self.external_trades,
                key=lambda t: self.external_max_gpt_id.get(t.TranNum, 0),
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error sorting external trades: {str(e)}")
            self.sorted_external_trades = self.external_trades.copy()
        
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
                
                # Store BOTH initial and current sensitivity (same at creation)
                sub_port.InitialSensitivity = dict(sensi_dict)
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
        Uses pre-computed cache for performance.
        
        Args:
            trade (TradeInfo): External trade
            
        Returns:
            List[SensitivityRecord]: Sensitivity records for this trade
        """
        return self.external_sensitivities_cache.get(trade.TranNum, [])
    
    def calculate_sensitivity_reduction(self, sub_port: SubPortfolio, external_trade: TradeInfo,
                                       external_sensi: List[SensitivityRecord], 
                                       remaining_usage: float = 1.0) -> float:
        """
        Calculate how much sensitivity would be reduced by matching with an external trade.
        Only considers sensitivities with the same Index and Tenor.
        
        For opposite WAY trades, sensitivities with opposite signs can offset each other:
        - Pay sub-portfolio with positive sensitivity + Rec external trade with negative sensitivity
        - Rec sub-portfolio with negative sensitivity + Pay external trade with positive sensitivity
        
        Args:
            sub_port (SubPortfolio): Internal sub-portfolio
            external_trade (TradeInfo): External trade to match with
            external_sensi (List[SensitivityRecord]): Sensitivities of the external trade
            remaining_usage (float): Remaining usage percentage (0.0 to 1.0) of the external trade
            
        Returns:
            float: Total sensitivity reduction score (higher is better)
        """
        # Create a dictionary of external sensitivities, adjusted by remaining usage
        external_sensi_dict = defaultdict(float)
        for sensi in external_sensi:
            external_sensi_dict[(sensi.Index, sensi.Tenor)] += sensi.Delta * remaining_usage
        
        # Calculate reduction for matching sensitivities
        reduction = 0.0
        for (index, tenor), delta in sub_port.TotalSensitivity.items():
            if (index, tenor) in external_sensi_dict:
                external_delta = external_sensi_dict[(index, tenor)]
                # Check if sensitivities have opposite signs (can offset each other)
                if delta * external_delta < 0:
                    # Sensitivities have opposite signs, can offset
                    reduction += min(abs(delta), abs(external_delta))
        
        return reduction
    
    def find_best_match(self, sub_port: SubPortfolio) -> Tuple[Optional[TradeInfo], List[SensitivityRecord], float]:
        """
        Find the best external trade to match with a sub-portfolio.
        Uses the algorithm: find external trades with opposite WAY that have matching Index/Tenor
        and reduce the sub-portfolio's total absolute sensitivity.
        
        Optimized to use pre-computed caches and only iterate through relevant trades.
        
        Args:
            sub_port (SubPortfolio): Internal sub-portfolio to match
            
        Returns:
            Tuple[Optional[TradeInfo], List[SensitivityRecord], float]: (best_trade, external_sensi, reduction_score)
        """
        # Extract WAY from sub-portfolio name
        parts = sub_port.Name.split('_')
        if len(parts) < 3:
            return None, [], 0.0
        
        sub_port_way = parts[2]
        
        # Use pre-sorted external trades and filter by opposite WAY
        # This avoids sorting in every iteration
        best_trade = None
        best_sensi = []
        best_reduction = 0.0
        
        for trade in self.sorted_external_trades:
            # Skip if not opposite WAY
            if trade.Way == sub_port_way:
                continue
            
            # Skip if already fully used
            current_usage = self.external_usage.get(trade.TranNum, 0.0)
            if current_usage >= 1.0:
                continue
            
            # Get cached sensitivities
            external_sensi = self.external_sensitivities_cache.get(trade.TranNum, [])
            if not external_sensi:
                continue
            
            # Calculate remaining usage
            remaining_usage = 1.0 - current_usage
            
            # Calculate reduction directly (no need to create adjusted SensitivityRecord objects)
            reduction = self.calculate_sensitivity_reduction(
                sub_port, trade, external_sensi, remaining_usage
            )
            
            if reduction > best_reduction:
                best_reduction = reduction
                best_trade = trade
                best_sensi = external_sensi
        
        return best_trade, best_sensi, best_reduction
    
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
                total_sensi = sum(abs(d) for d in sub_port.TotalSensitivity.values())
                logger.info(f"  Initial total sensitivity: {total_sensi:.2f}")
                
                # Iterative matching
                iteration = 0
                while iteration < 100:  # Max iterations to prevent infinite loop
                    best_trade, external_sensi, best_reduction = self.find_best_match(sub_port)
                    
                    if best_trade is None or best_reduction <= 0:
                        logger.info(f"  No more matches found for {sub_port_name}")
                        break
                    
                    # Create dictionary of external sensitivities
                    external_sensi_dict = defaultdict(float)
                    for sensi in external_sensi:
                        external_sensi_dict[(sensi.Index, sensi.Tenor)] += sensi.Delta
                    
                    # Calculate optimal usage percentage to avoid over-matching
                    # Find the maximum amount we can use without overshooting
                    usage = 1.0
                    for (index, tenor), delta in sub_port.TotalSensitivity.items():
                        if (index, tenor) in external_sensi_dict:
                            external_delta = external_sensi_dict[(index, tenor)]
                            if external_delta != 0:
                                # Calculate usage that would bring sub_port sensitivity to zero
                                optimal_usage = -delta / external_delta
                                # We can only use up to 100% and must be positive
                                if 0 < optimal_usage < usage:
                                    usage = optimal_usage
                    # Ensure usage is within bounds
                    usage = max(0.0, min(1.0, usage))
                    
                    # Update usage
                    self.external_usage[best_trade.TranNum] = usage
                    
                    # Record the match - only store essential info to reduce memory
                    match_record = {
                        'SubPortfolio': sub_port_name,
                        'External_TranNum': best_trade.TranNum,
                        'External_Usage_Percentage': usage * 100,  # Store as percentage
                        'Reduction': best_reduction
                    }
                    
                    self.matched_results.append(match_record)
                    
                    # Update sub-portfolio sensitivities (reduce by matched amount)
                    # We need to properly offset sensitivities with opposite signs
                    # Only iterate through sensitivities that actually match
                    for (index, tenor), delta in list(sub_port.TotalSensitivity.items()):
                        if (index, tenor) in external_sensi_dict:
                            external_delta = external_sensi_dict[(index, tenor)]
                            # Check if sensitivities have opposite signs (can offset each other)
                            if delta * external_delta < 0:
                                # Sensitivities have opposite signs, can offset
                                # Calculate how much to reduce
                                reduction_amount = min(abs(delta), abs(external_delta) * usage)
                                # Reduce the sub-portfolio sensitivity
                                if delta > 0:
                                    sub_port.TotalSensitivity[(index, tenor)] = delta - reduction_amount
                                else:
                                    sub_port.TotalSensitivity[(index, tenor)] = delta + reduction_amount
                                # Remove if close to zero
                                if abs(sub_port.TotalSensitivity[(index, tenor)]) < 0.01:
                                    del sub_port.TotalSensitivity[(index, tenor)]
                    
                    logger.info(f"  Iteration {iteration + 1}: Matched with trade {best_trade.TranNum}, reduction: {best_reduction:.2f}")
                    logger.info(f"  Remaining sensitivity pairs: {len(sub_port.TotalSensitivity)}")
                    logger.info(f"  Remaining total sensitivity: {sum(abs(d) for d in sub_port.TotalSensitivity.values()):.2f}")
                    
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
                - 'internal_sub_portfolios' (INITIAL sensitivities - before matching)
                - 'matched_trades'
                - 'external_usage'
                - 'unmatched_sensitivities' (REMAINING sensitivities - after matching)
        """
        try:
            # Create Internal Sub-Portfolios table - USE INITIAL SENSITIVITIES (before matching)
            internal_sub_portfolios_data = []
            for sub_port_name, sub_port in self.sub_portfolios.items():
                for (index, tenor), delta in sub_port.InitialSensitivity.items():
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
                        'External_Usage_Percentage': record['External_Usage_Percentage'],
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
                    'Usage_Percentage': usage
                })
            
            external_usage_df = pd.DataFrame(external_usage_data)
            
            # Create Unmatched Sensitivities table - USE REMAINING SENSITIVITIES (after matching)
            # Include ALL sensitivity pairs (even if zero) for visual check
            unmatched_data = []
            for sub_port_name, sub_port in self.sub_portfolios.items():
                # Get all Index/Tenor pairs from InitialSensitivity (to keep same structure)
                for (index, tenor) in sub_port.InitialSensitivity.keys():
                    # Get current sensitivity (from TotalSensitivity if exists, else 0)
                    delta = sub_port.TotalSensitivity.get((index, tenor), 0.0)
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
