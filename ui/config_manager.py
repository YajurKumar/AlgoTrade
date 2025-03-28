"""
Configuration management module for the algorithmic trading system.
This module provides functionality to load, save, and manage configuration settings.
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('config_manager')

class ConfigManager:
    """
    Class to manage configuration settings for the algorithmic trading system.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Parameters:
        -----------
        config_file : str, optional
            Path to a config file.
        """
        self.config_file = config_file
        self.config = {}
        
        # Default configuration
        self.default_config = {
            "zerodha": {
                "api_key": "",
                "api_secret": "",
                "redirect_url": "http://localhost:8080"
            },
            "data": {
                "default_source": "yahoo",
                "cache_dir": os.path.join(str(Path.home()), ".algo_trading", "cache")
            },
            "backtesting": {
                "default_capital": 100000.0,
                "default_commission": 0.1
            },
            "trading": {
                "default_mode": "paper",
                "risk_per_trade": 0.02
            },
            "ui": {
                "theme": "default",
                "log_level": "INFO"
            }
        }
        
        # Load config if provided
        if config_file:
            self.load_config(config_file)
        else:
            # Use default config
            self.config = self.default_config.copy()
    
    def load_config(self, config_file):
        """
        Load configuration from a file.
        
        Parameters:
        -----------
        config_file : str
            Path to the config file.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with default config to ensure all required fields exist
                self._merge_configs(self.config, self.default_config)
                self._merge_configs(self.config, loaded_config)
                
                logger.info(f"Loaded configuration from {config_file}")
                return True
            else:
                logger.warning(f"Config file {config_file} not found. Using default configuration.")
                self.config = self.default_config.copy()
                return False
        
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self.config = self.default_config.copy()
            return False
    
    def save_config(self, config_file=None):
        """
        Save configuration to a file.
        
        Parameters:
        -----------
        config_file : str, optional
            Path to the config file. If None, uses the instance's config_file.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        if config_file is None:
            config_file = self.config_file
        
        if config_file is None:
            logger.error("No config file specified")
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            logger.info(f"Saved configuration to {config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Parameters:
        -----------
        key : str
            Configuration key. Can be nested using dot notation (e.g., 'zerodha.api_key').
        default : any, optional
            Default value to return if key is not found.
            
        Returns:
        --------
        any
            Configuration value.
        """
        if '.' in key:
            # Handle nested keys
            parts = key.split('.')
            value = self.config
            
            for part in parts:
                if part not in value:
                    return default
                value = value[part]
            
            return value
        else:
            # Handle top-level keys
            return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Parameters:
        -----------
        key : str
            Configuration key. Can be nested using dot notation (e.g., 'zerodha.api_key').
        value : any
            Configuration value.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        try:
            if '.' in key:
                # Handle nested keys
                parts = key.split('.')
                config = self.config
                
                for part in parts[:-1]:
                    if part not in config:
                        config[part] = {}
                    config = config[part]
                
                config[parts[-1]] = value
            else:
                # Handle top-level keys
                self.config[key] = value
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting config value: {str(e)}")
            return False
    
    def _merge_configs(self, target, source):
        """
        Recursively merge source config into target config.
        
        Parameters:
        -----------
        target : dict
            Target configuration dictionary.
        source : dict
            Source configuration dictionary.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_configs(target[key], value)
            else:
                target[key] = value
    
    def create_default_config(self, config_file):
        """
        Create a default configuration file.
        
        Parameters:
        -----------
        config_file : str
            Path to the config file.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(self.default_config, f, indent=4)
            
            logger.info(f"Created default configuration at {config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating default config: {str(e)}")
            return False
