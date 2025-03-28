"""
Unit tests for the trading strategies.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.advanced import TrendFollowingStrategy, MeanReversionStrategy, BreakoutStrategy
from data_fetcher.factory import DataFetcherFactory
from data_fetcher.normalizer import add_technical_indicators

class TestStrategies(unittest.TestCase):
    """Test cases for the trading strategies."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Define test symbols
        self.symbol = "AAPL"
        
        # Fetch real data for testing
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=200)  # Need more data for proper testing
        
        factory = DataFetcherFactory()
        fetcher = factory.get_yahoo_fetcher()
        self.data = fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval="1d"
        )
        
        # Add technical indicators to the data
        self.data = add_technical_indicators(self.data)
    
    def test_trend_following_strategy(self):
        """Test the trend following strategy."""
        # Create a trend following strategy
        strategy = TrendFollowingStrategy(
            symbol=self.symbol,
            ema_short=20,
            ema_long=50,
            adx_period=14,
            adx_threshold=25,
            risk_per_trade=0.02,
            trailing_stop_pct=0.05
        )
        
        # Generate signals
        signals = strategy.generate_signals(self.data.copy())
        
        # Check that signals are generated
        self.assertIn('signal', signals.columns)
        
        # Check that signals are either -1, 0, or 1
        unique_signals = signals['signal'].unique()
        for signal in unique_signals:
            self.assertIn(signal, [-1, 0, 1])
        
        # Check that at least some signals are generated
        self.assertTrue((signals['signal'] != 0).any())
        
        # Check that the strategy has a name
        self.assertIsNotNone(strategy.name)
        self.assertGreater(len(strategy.name), 0)
    
    def test_mean_reversion_strategy(self):
        """Test the mean reversion strategy."""
        # Create a mean reversion strategy
        strategy = MeanReversionStrategy(
            symbol=self.symbol,
            bb_period=20,
            bb_std=2.0,
            rsi_period=14,
            rsi_oversold=30,
            rsi_overbought=70,
            risk_per_trade=0.02,
            take_profit_atr_multiple=2.0,
            stop_loss_atr_multiple=1.0
        )
        
        # Generate signals
        signals = strategy.generate_signals(self.data.copy())
        
        # Check that signals are generated
        self.assertIn('signal', signals.columns)
        
        # Check that signals are either -1, 0, or 1
        unique_signals = signals['signal'].unique()
        for signal in unique_signals:
            self.assertIn(signal, [-1, 0, 1])
        
        # Check that at least some signals are generated
        self.assertTrue((signals['signal'] != 0).any())
        
        # Check that the strategy has a name
        self.assertIsNotNone(strategy.name)
        self.assertGreater(len(strategy.name), 0)
    
    def test_breakout_strategy(self):
        """Test the breakout strategy."""
        # Create a breakout strategy
        strategy = BreakoutStrategy(
            symbol=self.symbol,
            channel_period=20,
            volume_factor=1.5,
            consolidation_factor=0.5,
            risk_per_trade=0.02,
            stop_loss_atr_multiple=1.5,
            take_profit_atr_multiple=3.0
        )
        
        # Generate signals
        signals = strategy.generate_signals(self.data.copy())
        
        # Check that signals are generated
        self.assertIn('signal', signals.columns)
        
        # Check that signals are either -1, 0, or 1
        unique_signals = signals['signal'].unique()
        for signal in unique_signals:
            self.assertIn(signal, [-1, 0, 1])
        
        # Check that the strategy has a name
        self.assertIsNotNone(strategy.name)
        self.assertGreater(len(strategy.name), 0)
    
    def test_strategy_position_sizing(self):
        """Test strategy position sizing."""
        # Create a strategy
        strategy = TrendFollowingStrategy(
            symbol=self.symbol,
            risk_per_trade=0.02  # 2% risk per trade
        )
        
        # Test position sizing
        price = 150.0
        stop_loss = 145.0
        account_equity = 10000.0
        
        # Calculate position size
        position_size = strategy.calculate_position_size(
            price=price,
            stop_loss=stop_loss,
            account_equity=account_equity
        )
        
        # Expected position size: (account_equity * risk_per_trade) / (price - stop_loss)
        expected_size = (account_equity * 0.02) / (price - stop_loss)
        
        # Check that position size is calculated correctly
        self.assertAlmostEqual(position_size, expected_size, places=4)
        
        # Check that position size is reasonable
        self.assertGreater(position_size, 0)
        self.assertLess(position_size * price, account_equity)  # Position value should be less than account equity

if __name__ == '__main__':
    unittest.main()
