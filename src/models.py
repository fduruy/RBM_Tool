"""
models.py - Data models for RBM_Tool

This module contains the data classes used throughout the application:
- SensitivityRecord: Represents a single sensitivity record
- TradeInfo: Represents a trade with its information
- SubPortfolio: Represents an Internal Sub-Portfolio with trades and sensitivities
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class SensitivityRecord:
    """
    Represents a single sensitivity record from Rep_Sensi.csv
    
    Attributes:
        TranNum (int): Trade number
        InsNum (int): Instrument number
        Index (str): Index name (e.g., 'Estr', 'Sonia')
        Tenor (str): Tenor (e.g., '1Y', '5Y', '10Y')
        Gpt_Id (int): Group ID
        Delta (float): Sensitivity value
        Used (float): Percentage used in matching (0.0 to 1.0), default 0.0
    """
    TranNum: int
    InsNum: int
    Index: str
    Tenor: str
    Gpt_Id: int
    Delta: float
    Used: float = 0.0


@dataclass
class TradeInfo:
    """
    Represents a trade with its information from GT_Valo.csv
    
    Attributes:
        TranNum (int): Trade number
        InsNum (int): Instrument number
        ExternalParty (str): Counterparty (e.g., 'CLFRFRPP', 'Bank')
        PricingModel (str): Pricing model (e.g., 'Inflation', 'Discounting')
        MTM (float): Mark-to-Market value
        CCY (str): Currency (e.g., 'EUR', 'GBP', 'USD')
        Way (str): Direction ('Pay' or 'Rec')
        IsInternal (bool): Whether this is an internal trade
    """
    TranNum: int
    InsNum: int
    ExternalParty: str
    PricingModel: str
    MTM: float
    CCY: str
    Way: str
    IsInternal: bool


@dataclass
class SubPortfolio:
    """
    Represents an Internal Sub-Portfolio
    
    Attributes:
        Name (str): Sub-portfolio name (format: CCY_PricingModel_Way)
        Trades (List[TradeInfo]): List of trades in this sub-portfolio
        Sensitivities (List[SensitivityRecord]): List of sensitivity records
        InitialSensitivity (Dict[Tuple[str, str], float]): Initial aggregated sensitivity per (Index, Tenor)
        TotalSensitivity (Dict[Tuple[str, str], float]): Current aggregated sensitivity per (Index, Tenor)
    """
    Name: str
    Trades: List[TradeInfo]
    Sensitivities: List[SensitivityRecord]
    InitialSensitivity: Dict[Tuple[str, str], float] = field(default_factory=dict)
    TotalSensitivity: Dict[Tuple[str, str], float] = field(default_factory=dict)
