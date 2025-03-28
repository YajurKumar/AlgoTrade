"""
Command-line interface for the algorithmic trading system.
This module provides a user-friendly interface to interact with the trading system.
"""

import os
import sys
import cmd
import json
import logging
import argparse
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from tabulate import tabulate

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from backtesting.base import Backtester
from strategies.advanced import TrendFollowingStrategy, MeanReversionStrategy, BreakoutStrategy
from zerodha_integration.trading_engine import TradingEngine

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('cli')

class AlgoTradingCLI(cmd.Cmd):
    """
    Command-line interface for the algorithmic trading system.
    """
    
    intro = """
    ======================================================
    Algorithmic Trading System - Command Line Interface
    ======================================================
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit.
    """
    
    prompt = 'algo-trading> '
    
    def __init__(self, config_file=None):
        """
        Initialize the CLI.
        
        Parameters:
        -----------
        config_file : str, optional
            Path to a config file.
        """
        super().__init__()
        self.config_file = config_file
        self.config = {}
        
        # Load config if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
        # Initialize components
        self.data_factory = DataFetcherFactory()
        self.data_fetcher = None
        self.trading_engine = None
        self.strategies = {}
        self.current_data = {}
        
        # Initialize data fetcher
        self.data_fetcher = self.data_factory.get_yahoo_fetcher()
        
        # Initialize trading engine
        self.init_trading_engine()
    
    def init_trading_engine(self):
        """
        Initialize the trading engine.
        """
        # Get Zerodha credentials from config
        api_key = self.config.get('zerodha', {}).get('api_key')
        api_secret = self.config.get('zerodha', {}).get('api_secret')
        redirect_url = self.config.get('zerodha', {}).get('redirect_url')
        
        # Initialize trading engine
        self.trading_engine = TradingEngine(
            api_key=api_key,
            api_secret=api_secret,
            redirect_url=redirect_url,
            config_file=self.config_file
        )
        
        logger.info("Initialized trading engine")
    
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
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            logger.info(f"Loaded configuration from {config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
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
    
    def do_exit(self, arg):
        """Exit the program."""
        print("Exiting...")
        return True
    
    def do_quit(self, arg):
        """Exit the program."""
        return self.do_exit(arg)
    
    def do_config(self, arg):
        """
        Manage configuration.
        
        Usage:
            config show                   - Show current configuration
            config set <key> <value>      - Set a configuration value
            config save [<file>]          - Save configuration to file
            config load <file>            - Load configuration from file
        """
        args = arg.split()
        
        if not args:
            print("Error: No subcommand specified")
            print(self.do_config.__doc__)
            return
        
        subcommand = args[0]
        
        if subcommand == 'show':
            print(json.dumps(self.config, indent=4))
        
        elif subcommand == 'set':
            if len(args) < 3:
                print("Error: Missing key or value")
                return
            
            key = args[1]
            value = ' '.join(args[2:])
            
            # Handle nested keys (e.g., 'zerodha.api_key')
            if '.' in key:
                parts = key.split('.')
                current = self.config
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                current[parts[-1]] = value
            else:
                self.config[key] = value
            
            print(f"Set {key} = {value}")
        
        elif subcommand == 'save':
            if len(args) > 1:
                file_path = args[1]
            else:
                file_path = self.config_file
            
            if not file_path:
                print("Error: No config file specified")
                return
            
            if self.save_config(file_path):
                print(f"Configuration saved to {file_path}")
            else:
                print("Error saving configuration")
        
        elif subcommand == 'load':
            if len(args) < 2:
                print("Error: No file specified")
                return
            
            file_path = args[1]
            
            if self.load_config(file_path):
                self.config_file = file_path
                print(f"Configuration loaded from {file_path}")
                
                # Reinitialize components with new config
                self.init_trading_engine()
            else:
                print("Error loading configuration")
        
        else:
            print(f"Error: Unknown subcommand '{subcommand}'")
            print(self.do_config.__doc__)
    
    def do_zerodha(self, arg):
        """
        Manage Zerodha integration.
        
        Usage:
            zerodha login                 - Login to Zerodha
            zerodha complete <url>        - Complete login with redirect URL
            zerodha status                - Check authentication status
            zerodha logout                - Logout from Zerodha
        """
        args = arg.split()
        
        if not args:
            print("Error: No subcommand specified")
            print(self.do_zerodha.__doc__)
            return
        
        subcommand = args[0]
        
        if subcommand == 'login':
            if not self.trading_engine:
                print("Error: Trading engine not initialized")
                return
            
            login_url = self.trading_engine.login(open_browser=False)
            print(f"Please visit the following URL to login:")
            print(login_url)
            print("\nAfter login, you will be redirected to a URL. Copy that URL and use 'zerodha complete <url>' to complete the login process.")
        
        elif subcommand == 'complete':
            if not self.trading_engine:
                print("Error: Trading engine not initialized")
                return
            
            if len(args) < 2:
                print("Error: No redirect URL specified")
                return
            
            redirect_url = args[1]
            
            if self.trading_engine.complete_login(redirect_url):
                print("Login completed successfully")
            else:
                print("Error completing login")
        
        elif subcommand == 'status':
            if not self.trading_engine:
                print("Error: Trading engine not initialized")
                return
            
            if self.trading_engine.is_authenticated():
                print("Authenticated with Zerodha")
            else:
                print("Not authenticated with Zerodha")
        
        elif subcommand == 'logout':
            if not self.trading_engine:
                print("Error: Trading engine not initialized")
                return
            
            if self.trading_engine.auth.logout():
                print("Logged out successfully")
            else:
                print("Error logging out")
        
        else:
            print(f"Error: Unknown subcommand '{subcommand}'")
            print(self.do_zerodha.__doc__)
    
    def do_data(self, arg):
        """
        Fetch and manage market data.
        
        Usage:
            data fetch <symbol> <days> [<interval>]   - Fetch historical data
            data show [<symbol>]                      - Show fetched data
            data save <symbol> <filename>             - Save data to CSV
            data load <symbol> <filename>             - Load data from CSV
        """
        args = arg.split()
        
        if not args:
            print("Error: No subcommand specified")
            print(self.do_data.__doc__)
            return
        
        subcommand = args[0]
        
        if subcommand == 'fetch':
            if len(args) < 3:
                print("Error: Missing symbol or days")
                return
            
            symbol = args[1]
            days = int(args[2])
            interval = args[3] if len(args) > 3 else '1d'
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            print(f"Fetching {days} days of {interval} data for {symbol}...")
            
            if self.trading_engine and self.trading_engine.is_authenticated():
                # Use Zerodha for authenticated users
                data = self.trading_engine.get_historical_data(
                    symbol=symbol,
                    from_date=start_date,
                    to_date=end_date,
                    interval=interval
                )
            else:
                # Use Yahoo Finance as fallback
                data = self.data_fetcher.fetch_historical_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    interval=interval
                )
            
            if data.empty:
                print("No data fetched. Please check the symbol and date range.")
                return
            
            self.current_data[symbol] = data
            print(f"Fetched {len(data)} data points")
        
        elif subcommand == 'show':
            if len(args) > 1:
                symbol = args[1]
                if symbol not in self.current_data:
                    print(f"No data for {symbol}. Fetch it first.")
                    return
                
                data = self.current_data[symbol]
                print(f"Data for {symbol} ({len(data)} points):")
                print(data.head(10))
                
                if len(data) > 10:
                    print("...")
                    print(data.tail(5))
            else:
                if not self.current_data:
                    print("No data fetched yet.")
                    return
                
                print("Available data:")
                for symbol, data in self.current_data.items():
                    print(f"  {symbol}: {len(data)} points from {data.index[0]} to {data.index[-1]}")
        
        elif subcommand == 'save':
            if len(args) < 3:
                print("Error: Missing symbol or filename")
                return
            
            symbol = args[1]
            filename = args[2]
            
            if symbol not in self.current_data:
                print(f"No data for {symbol}. Fetch it first.")
                return
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            self.current_data[symbol].to_csv(filename)
            print(f"Saved data for {symbol} to {filename}")
        
        elif subcommand == 'load':
            if len(args) < 3:
                print("Error: Missing symbol or filename")
                return
            
            symbol = args[1]
            filename = args[2]
            
            try:
                data = pd.read_csv(filename, index_col=0, parse_dates=True)
                self.current_data[symbol] = data
                print(f"Loaded {len(data)} data points for {symbol} from {filename}")
            except Exception as e:
                print(f"Error loading data: {str(e)}")
        
        else:
            print(f"Error: Unknown subcommand '{subcommand}'")
            print(self.do_data.__doc__)
    
    def do_strategy(self, arg):
        """
        Manage trading strategies.
        
        Usage:
            strategy list                                 - List available strategies
            strategy create <name> <type> <symbol> [<params>]  - Create a strategy
            strategy show <name>                          - Show strategy details
            strategy delete <name>                        - Delete a strategy
        """
        args = arg.split()
        
        if not args:
            print("Error: No subcommand specified")
            print(self.do_strategy.__doc__)
            return
        
        subcommand = args[0]
        
        if subcommand == 'list':
            if not self.strategies:
                print("No strategies created yet.")
                return
            
            print("Available strategies:")
            for name, strategy in self.strategies.items():
                print(f"  {name}: {strategy.__class__.__name__} for {strategy.symbol}")
        
        elif subcommand == 'create':
            if len(args) < 4:
                print("Error: Missing name, type, or symbol")
                return
            
            name = args[1]
            strategy_type = args[2]
            symbol = args[3]
            
            # Parse additional parameters
            params = {}
            for param in args[4:]:
                if '=' in param:
                    key, value = param.split('=', 1)
                    
                    # Convert value to appropriate type
                    try:
                        if '.' in value:
                            params[key] = float(value)
                        else:
                            params<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>