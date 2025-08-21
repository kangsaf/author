"""
Utility functions for kang_bot trading system
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

def load_json(file_path: str, default: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """
    Load JSON file with error handling
    
    Args:
        file_path (str): Path to JSON file
        default (dict): Default value if file not found or invalid
        
    Returns:
        dict: Loaded JSON data or default value
    """
    if default is None:
        default = {}
        
    try:
        if not os.path.exists(file_path):
            logging.warning(f"Config file not found: {file_path}, using default")
            return default
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logging.error(f"Error loading JSON from {file_path}: {e}")
        return default

def save_json(file_path: str, data: Dict[Any, Any]) -> bool:
    """
    Save data to JSON file with error handling
    
    Args:
        file_path (str): Path to save JSON file
        data (dict): Data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON to {file_path}: {e}")
        return False

def get_jakarta_time() -> datetime:
    """
    Get current time in Jakarta timezone
    
    Returns:
        datetime: Current Jakarta time
    """
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

def format_currency(amount: float, symbol: str = "USDT") -> str:
    """
    Format currency amount for display
    
    Args:
        amount (float): Amount to format
        symbol (str): Currency symbol
        
    Returns:
        str: Formatted currency string
    """
    return f"{amount:.4f} {symbol}"

def calculate_percentage(current: float, previous: float) -> float:
    """
    Calculate percentage change
    
    Args:
        current (float): Current value
        previous (float): Previous value
        
    Returns:
        float: Percentage change
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100

def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize trading symbol
    
    Args:
        symbol (str): Trading symbol
        
    Returns:
        str: Normalized symbol
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    
    symbol = symbol.upper().strip()
    
    # Basic validation for common patterns
    if not symbol.endswith('USDT') and not symbol.endswith('BUSD'):
        # Add USDT if no quote currency specified
        symbol += 'USDT'
    
    return symbol

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default (float): Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration
    
    Args:
        log_level (str): Logging level
    """
    # Ensure logs directory exists
    os.makedirs('/workspace/logs', exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Setup file handlers
    trading_handler = logging.FileHandler('/workspace/logs/trading.log')
    trading_handler.setFormatter(logging.Formatter(log_format))
    
    error_handler = logging.FileHandler('/workspace/logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format))
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[trading_handler, error_handler, console_handler],
        format=log_format
    )

class ConfigManager:
    """Configuration manager for kang_bot"""
    
    def __init__(self, config_dir: str = "/workspace/config"):
        self.config_dir = config_dir
        self._config_cache = {}
    
    def get_config(self, config_name: str = "config") -> Dict[Any, Any]:
        """
        Get configuration by name
        
        Args:
            config_name (str): Configuration name
            
        Returns:
            dict: Configuration data
        """
        config_file = os.path.join(self.config_dir, f"{config_name}.json")
        
        # Check cache first
        if config_file in self._config_cache:
            return self._config_cache[config_file]
        
        # Load from file
        config = load_json(config_file, {})
        self._config_cache[config_file] = config
        
        return config
    
    def save_config(self, config_name: str, data: Dict[Any, Any]) -> bool:
        """
        Save configuration
        
        Args:
            config_name (str): Configuration name
            data (dict): Configuration data
            
        Returns:
            bool: True if successful
        """
        config_file = os.path.join(self.config_dir, f"{config_name}.json")
        
        if save_json(config_file, data):
            # Update cache
            self._config_cache[config_file] = data
            return True
        
        return False
    
    def reload_config(self, config_name: str = None) -> None:
        """
        Reload configuration from file
        
        Args:
            config_name (str): Specific config to reload, None for all
        """
        if config_name:
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            if config_file in self._config_cache:
                del self._config_cache[config_file]
        else:
            self._config_cache.clear()

# Global config manager instance
config_manager = ConfigManager()