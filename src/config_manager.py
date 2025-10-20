"""
Configuration Manager
Loads and validates configuration
"""

import yaml
import os
from typing import Dict, Any
import logging


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, 'config', 'config.yaml')
        
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Returns:
            Configuration dictionary
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate configuration
        self.validate_config(config)
        
        return config
    
    def validate_config(self, config: Dict[str, Any]):
        """
        Validate configuration structure and values
        
        Args:
            config: Configuration dictionary to validate
        """
        required_sections = ['mt5', 'smc', 'trading', 'logging']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate trading section
        trading = config['trading']
        if not trading.get('symbols'):
            raise ValueError("No trading symbols specified")
        
        if trading.get('lot_size', 0) <= 0:
            raise ValueError("Invalid lot_size")
        
        if trading.get('max_positions', 0) <= 0:
            raise ValueError("Invalid max_positions")
        
        # Validate timeframe
        valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']
        if trading.get('timeframe') not in valid_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
    
    def get(self, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Dot-separated key path (e.g., 'mt5.account')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if key is None:
            return self.config
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
