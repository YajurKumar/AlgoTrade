"""
Integration tests for the algorithmic trading system.
"""

import os
import sys
import unittest
import pandas as pd
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from backtesting.base import Backtester
from strategies.advanced import TrendFollowingStrategy, MeanReversionStrategy, BreakoutStrategy
from zerodha_integration.trading_engine import TradingEngine
from ui.config_manager import ConfigManager

class TestIntegration(unittest.TestCase):
    """Integration tests for the algorithmic trading system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Define test symbols
        self.symbol = "AAPL"
        
        # Fetch real data for testing
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=200)  # Need more data for proper testing
        
        self.factory = DataFetcherFactory()
        self.fetcher = self.factory.get_yahoo_fetcher()
        self.data = self.fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval="1d"
        )
        
        # Create strategies
        self.trend_strategy = TrendFollowingStrategy(symbol=self.symbol)
        self.mean_reversion_strategy = MeanReversionStrategy(symbol=self.symbol)
        self.breakout_strategy = BreakoutStrategy(symbol=self.symbol)
        
        # Create config manager
        self.config_manager = ConfigManager()
        
        # Create trading engine (paper trading mode)
        self.trading_engine = TradingEngine()
    
    def test_data_fetching_to_backtesting_integration(self):
        """Test integration between data fetching and backtesting."""
        # Fetch data
        data = self.fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval="1d"
        )
        
        # Check that data is not empty
        self.assertFalse(data.empty)
        
        # Create backtester with trend following strategy
        backtester = Backtester(
            strategy=self.trend_strategy,
            data={self.symbol: data},
            initial_capital=10000.0,
            commission=0.001
        )
        
        # Run backtest
        results = backtester.run()
        
        # Check that results are generated
        self.assertIsNotNone(results)
        self.assertIn('total_return', results)
        self.assertIn('equity_curve', results)
        
        # Check that equity curve has the same length as data
        self.assertEqual(len(results['equity_curve']), len(data))
    
    def test_strategy_to_backtesting_integration(self):
        """Test integration between strategies and backtesting."""
        # Test all strategies
        strategies = [
            self.trend_strategy,
            self.mean_reversion_strategy,
            self.breakout_strategy
        ]
        
        for strategy in strategies:
            # Create backtester
            backtester = Backtester(
                strategy=strategy,
                data={self.symbol: self.data},
                initial_capital=10000.0,
                commission=0.001
            )
            
            # Run backtest
            results = backtester.run()
            
            # Check that results are generated
            self.assertIsNotNone(results)
            self.assertIn('total_return', results)
            self.assertIn('equity_curve', results)
            
            # Check that trades were generated
            self.assertGreater(results['num_trades'], 0)
    
    def test_trading_engine_paper_mode(self):
        """Test trading engine in paper trading mode."""
        # Add a strategy to the trading engine
        self.trading_engine.add_strategy(self.trend_strategy)
        
        # Add symbol to watchlist
        self.trading_engine.add_to_watchlist(self.symbol)
        
        # Start trading engine in paper mode
        self.trading_engine.start(mode='paper')
        
        # Check that trading engine is running
        self.assertTrue(self.trading_engine.running)
        self.assertEqual(self.trading_engine.mode, 'paper')
        
        # Place a test order
        order_id = self.trading_engine.place_order(
            symbol=self.symbol,
            exchange="NSE",
            transaction_type=self.trading_engine.order_manager.TransactionType.BUY,
            quantity=10,
            order_type=self.trading_engine.order_manager.OrderType.MARKET
        )
        
        # Check that order was placed
        self.assertIsNotNone(order_id)
        
        # Get orders
        orders = self.trading_engine.get_orders()
        
        # Check that order exists
        self.assertIn(order_id, orders)
        
        # Get positions
        positions = self.trading_engine.get_positions()
        
        # Check that position exists
        self.assertGreater(len(positions), 0)
        
        # Stop trading engine
        self.trading_engine.stop()
        
        # Check that trading engine is stopped
        self.assertFalse(self.trading_engine.running)
    
    def test_config_manager(self):
        """Test configuration manager."""
        # Set some config values
        self.config_manager.set('zerodha.api_key', 'test_api_key')
        self.config_manager.set('zerodha.api_secret', 'test_api_secret')
        self.config_manager.set('trading.default_mode', 'paper')
        
        # Get config values
        api_key = self.config_manager.get('zerodha.api_key')
        api_secret = self.config_manager.get('zerodha.api_secret')
        default_mode = self.config_manager.get('trading.default_mode')
        
        # Check that values are set correctly
        self.assertEqual(api_key, 'test_api_key')
        self.assertEqual(api_secret, 'test_api_secret')
        self.assertEqual(default_mode, 'paper')
        
        # Test saving and loading config
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
            temp_path = temp.name
        
        try:
            # Save config
            self.config_manager.config_file = temp_path
            self.config_manager.save_config()
            
            # Create a new config manager and load the config
            new_config = ConfigManager(config_file=temp_path)
            
            # Check that values are loaded correctly
            self.assertEqual(new_config.get('zerodha.api_key'), 'test_api_key')
            self.assertEqual(new_config.get('zerodha.api_secret'), 'test_api_secret')
            self.assertEqual(new_config.get('trading.default_mode'), 'paper')
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
