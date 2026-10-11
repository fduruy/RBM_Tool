"""
config_loader.py - Module for loading and managing configuration for RBM_Tool

This module handles:
- Loading configuration from JSON files
- Validating configuration structure
- Providing access to configuration rules for Index, Tenor, SubPortfolio
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Main class for loading and managing RBM_Tool configuration.
    
    This class provides access to all configuration rules defined in config.json.
    """
    
    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigLoader.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                                        If None, uses default path.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self._validate_config_path()
        
    def _validate_config_path(self) -> None:
        """
        Validate that the config path exists and is readable.
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found at {self.config_path}")
            # Create default config if not exists
            self._create_default_config()
        
    def _create_default_config(self) -> None:
        """
        Create a default configuration file if it doesn't exist.
        """
        default_config = {
            "version": "1.0",
            "description": "Default RBM_Tool configuration",
            "rules": {
                "Index": {
                    "allowed_indexes": ["Estr", "Sonia", "Euribor", "Libor"],
                    "case_sensitive": False,
                    "normalize_case": "upper"
                },
                "Tenor": {
                    "allowed_tenors": ["ON", "TN", "1W", "1M", "1Y"],
                    "case_sensitive": False,
                    "normalize_case": "upper"
                },
                "SubPortfolio": {
                    "naming_convention": {
                        "format": "{CCY}_{PricingModel}_{Way}",
                        "separator": "_"
                    }
                }
            }
        }
        
        # Ensure directory exists
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default configuration at {self.config_path}")
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            bool: True if configuration was loaded successfully
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._validate_config()
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def _validate_config(self) -> bool:
        """
        Validate the loaded configuration structure.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check for required top-level keys
            if 'rules' not in self.config:
                logger.warning("Configuration missing 'rules' section")
                return False
            
            rules = self.config.get('rules', {})
            
            # Validate Index rules
            if 'Index' not in rules:
                logger.warning("Configuration missing 'Index' rules")
            
            # Validate Tenor rules
            if 'Tenor' not in rules:
                logger.warning("Configuration missing 'Tenor' rules")
            
            # Validate SubPortfolio rules
            if 'SubPortfolio' not in rules:
                logger.warning("Configuration missing 'SubPortfolio' rules")
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration dictionary.
        
        Returns:
            Dict[str, Any]: Complete configuration
        """
        return self.config
    
    def get_index_rules(self) -> Dict[str, Any]:
        """
        Get Index-related rules.
        
        Returns:
            Dict[str, Any]: Index configuration rules
        """
        return self.config.get('rules', {}).get('Index', {})
    
    def get_tenor_rules(self) -> Dict[str, Any]:
        """
        Get Tenor-related rules.
        
        Returns:
            Dict[str, Any]: Tenor configuration rules
        """
        return self.config.get('rules', {}).get('Tenor', {})
    
    def get_subportfolio_rules(self) -> Dict[str, Any]:
        """
        Get SubPortfolio-related rules.
        
        Returns:
            Dict[str, Any]: SubPortfolio configuration rules
        """
        return self.config.get('rules', {}).get('SubPortfolio', {})
    
    def get_internal_trades_rules(self) -> Dict[str, Any]:
        """
        Get InternalTrades-related rules.
        
        Returns:
            Dict[str, Any]: InternalTrades configuration rules
        """
        return self.config.get('rules', {}).get('InternalTrades', {})
    
    def get_external_trades_rules(self) -> Dict[str, Any]:
        """
        Get ExternalTrades-related rules.
        
        Returns:
            Dict[str, Any]: ExternalTrades configuration rules
        """
        return self.config.get('rules', {}).get('ExternalTrades', {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get global validation rules.
        
        Returns:
            Dict[str, Any]: Validation configuration rules
        """
        return self.config.get('Validation', {})
    
    def get_output_rules(self) -> Dict[str, Any]:
        """
        Get output formatting rules.
        
        Returns:
            Dict[str, Any]: Output configuration rules
        """
        return self.config.get('rules', {}).get('Output', {})
    
    def get_allowed_indexes(self) -> List[str]:
        """
        Get list of allowed Index values.
        
        Returns:
            List[str]: List of allowed indexes
        """
        index_rules = self.get_index_rules()
        return index_rules.get('allowed_indexes', [])
    
    def get_allowed_tenors(self) -> List[str]:
        """
        Get list of allowed Tenor values.
        
        Returns:
            List[str]: List of allowed tenors
        """
        tenor_rules = self.get_tenor_rules()
        return tenor_rules.get('allowed_tenors', [])
    
    def is_index_allowed(self, index: str) -> bool:
        """
        Check if an index is allowed according to configuration.
        
        Args:
            index (str): Index to check
            
        Returns:
            bool: True if index is allowed
        """
        allowed_indexes = self.get_allowed_indexes()
        index_rules = self.get_index_rules()
        
        # Apply case normalization if configured
        if not index_rules.get('case_sensitive', True):
            normalize_to = index_rules.get('normalize_case', 'upper')
            if normalize_to == 'upper':
                index = index.upper()
            elif normalize_to == 'lower':
                index = index.lower()
            
            allowed_indexes = [
                idx.upper() if normalize_to == 'upper' else idx.lower() 
                for idx in allowed_indexes
            ]
        
        # Check in allowed list
        if index in allowed_indexes:
            return True
        
        # Check aliases
        aliases = index_rules.get('aliases', {})
        if index in aliases:
            normalized_alias = aliases[index]
            if not index_rules.get('case_sensitive', True):
                if normalize_to == 'upper':
                    normalized_alias = normalized_alias.upper()
                elif normalize_to == 'lower':
                    normalized_alias = normalized_alias.lower()
            return normalized_alias in allowed_indexes
        
        return False
    
    def is_tenor_allowed(self, tenor: str) -> bool:
        """
        Check if a tenor is allowed according to configuration.
        
        Args:
            tenor (str): Tenor to check
            
        Returns:
            bool: True if tenor is allowed
        """
        allowed_tenors = self.get_allowed_tenors()
        tenor_rules = self.get_tenor_rules()
        
        # Apply case normalization if configured
        if not tenor_rules.get('case_sensitive', True):
            normalize_to = tenor_rules.get('normalize_case', 'upper')
            if normalize_to == 'upper':
                tenor = tenor.upper()
            elif normalize_to == 'lower':
                tenor = tenor.lower()
            
            allowed_tenors = [
                t.upper() if normalize_to == 'upper' else t.lower() 
                for t in allowed_tenors
            ]
        
        # Check in allowed list
        if tenor in allowed_tenors:
            return True
        
        # Check aliases
        aliases = tenor_rules.get('aliases', {})
        if tenor in aliases:
            return True
        
        return False
    
    def normalize_index(self, index: str) -> str:
        """
        Normalize an index according to configuration rules.
        
        Args:
            index (str): Index to normalize
            
        Returns:
            str: Normalized index
        """
        index_rules = self.get_index_rules()
        
        # Apply aliases first
        aliases = index_rules.get('aliases', {})
        if index in aliases:
            index = aliases[index]
        
        # Apply case normalization
        if not index_rules.get('case_sensitive', True):
            normalize_to = index_rules.get('normalize_case', 'upper')
            if normalize_to == 'upper':
                return index.upper()
            elif normalize_to == 'lower':
                return index.lower()
        
        return index
    
    def normalize_tenor(self, tenor: str) -> str:
        """
        Normalize a tenor according to configuration rules.
        
        Args:
            tenor (str): Tenor to normalize
            
        Returns:
            str: Normalized tenor
        """
        tenor_rules = self.get_tenor_rules()
        
        # Apply aliases first
        aliases = tenor_rules.get('aliases', {})
        if tenor in aliases:
            tenor = aliases[tenor]
        
        # Apply case normalization
        if not tenor_rules.get('case_sensitive', True):
            normalize_to = tenor_rules.get('normalize_case', 'upper')
            if normalize_to == 'upper':
                tenor = tenor.upper()
            elif normalize_to == 'lower':
                tenor = tenor.lower()
        
        # Apply conversions if enabled
        if tenor_rules.get('conversion', {}).get('enable', False):
            # Convert months to years
            months_to_years = tenor_rules.get('conversion', {}).get('months_to_years', {})
            if tenor in months_to_years:
                return months_to_years[tenor]
            
            # Convert weeks to months
            weeks_to_months = tenor_rules.get('conversion', {}).get('weeks_to_months', {})
            if tenor in weeks_to_months:
                return weeks_to_months[tenor]
        
        return tenor
    
    def get_subportfolio_naming_format(self) -> str:
        """
        Get the sub-portfolio naming format.
        
        Returns:
            str: Naming format string
        """
        subportfolio_rules = self.get_subportfolio_rules()
        naming = subportfolio_rules.get('naming_convention', {})
        return naming.get('format', '{CCY}_{PricingModel}_{Way}')
    
    def get_subportfolio_grouping_keys(self) -> List[str]:
        """
        Get the primary grouping keys for sub-portfolios.
        
        Returns:
            List[str]: List of grouping keys
        """
        subportfolio_rules = self.get_subportfolio_rules()
        grouping = subportfolio_rules.get('grouping', {})
        return grouping.get('primary_key', ['CCY', 'PricingModel', 'Way'])
    
    def get_matching_algorithm_config(self) -> Dict[str, Any]:
        """
        Get the matching algorithm configuration.
        
        Returns:
            Dict[str, Any]: Matching algorithm configuration
        """
        subportfolio_rules = self.get_subportfolio_rules()
        return subportfolio_rules.get('matching', {}).get('algorithm', {})
    
    def get_specific_subportfolio_rules(self, subportfolio_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific rules for a named sub-portfolio.
        
        Args:
            subportfolio_name (str): Name of the sub-portfolio
            
        Returns:
            Optional[Dict[str, Any]]: Specific rules or None if not found
        """
        subportfolio_rules = self.get_subportfolio_rules()
        specific_rules = subportfolio_rules.get('specific_subportfolios', {}).get('rules', [])
        
        for rule in specific_rules:
            if rule.get('name') == subportfolio_name:
                return rule
        
        return None
    
    def get_internal_trades_patterns(self) -> List[str]:
        """
        Get patterns for identifying internal trades.
        
        Returns:
            List[str]: List of patterns
        """
        internal_rules = self.get_internal_trades_rules()
        identification = internal_rules.get('identification', {})
        return identification.get('external_party_patterns', ['CLF.*', 'FSA.*'])


# Global configuration instance
config_loader = None


def load_configuration(config_path: Optional[str] = None) -> Optional[ConfigLoader]:
    """
    Load and return the configuration.
    
    Args:
        config_path (str, optional): Path to configuration file
        
    Returns:
        Optional[ConfigLoader]: Loaded configuration or None on error
    """
    global config_loader
    
    if config_loader is None:
        config_loader = ConfigLoader(config_path)
        if not config_loader.load():
            return None
    
    return config_loader


def get_config() -> Optional[ConfigLoader]:
    """
    Get the global configuration instance.
    
    Returns:
        Optional[ConfigLoader]: Global configuration instance
    """
    global config_loader
    return config_loader


# Example usage (for testing)
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING CONFIG LOADER")
    print("=" * 60)
    
    # Load configuration
    config = load_configuration()
    
    if config:
        print("\nConfiguration loaded successfully!")
        print(f"\nVersion: {config.config.get('version')}")
        print(f"Description: {config.config.get('description')}")
        
        print(f"\nAllowed Indexes: {config.get_allowed_indexes()}")
        print(f"Allowed Tenors: {config.get_allowed_tenors()}")
        
        print(f"\nIs 'Estr' allowed? {config.is_index_allowed('Estr')}")
        print(f"Is 'EURIBOR' allowed? {config.is_index_allowed('EURIBOR')}")
        print(f"Normalize 'euribor': {config.normalize_index('euribor')}")
        
        print(f"\nIs '1Y' allowed? {config.is_tenor_allowed('1Y')}")
        print(f"Is '12M' allowed? {config.is_tenor_allowed('12M')}")
        print(f"Normalize '12 Months': {config.normalize_tenor('12 Months')}")
        
        print(f"\nSubPortfolio naming format: {config.get_subportfolio_naming_format()}")
        print(f"SubPortfolio grouping keys: {config.get_subportfolio_grouping_keys()}")
    else:
        print("\nFailed to load configuration")
