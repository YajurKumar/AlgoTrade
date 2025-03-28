"""
Unit tests for the data fetcher module.
"""

import os
import sys
import unittest
import pandas as pd
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from data_fetcher.yahoo_finance import YahooFinanceFetcher
from data_fetcher.normalizer import normalize_data, add_technical_indicators

class TestDataFetcher(unittest.TestCase):
    """Test cases for the data fetcher module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = DataFetcherFactory()
        self.yahoo_fetcher = self.factory.get_yahoo_fetcher()
        
        # Test data parameters
        self.symbol = "AAPL"
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)
        self.interval = "1d"
    
    def test_factory_creation(self):
        """Test that the factory creates the correct fetcher types."""
        yahoo_fetcher = self.factory.get_yahoo_fetcher()
        self.assertIsInstance(yahoo_fetcher, YahooFinanceFetcher)
    
    def test_yahoo_fetcher(self):
        """Test that the Yahoo Finance fetcher can retrieve data."""
        data = self.yahoo_fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval=self.interval
        )
        
        # Check that we got data
        self.assertFalse(data.empty)
        
        # Check that the data has the expected columns
        expected_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in expected_columns:
            self.assertIn(col, data.columns)
        
        # Check that the data has the expected date range
        # Allow for weekends and holidays by checking that the date range is reasonable
        self.assertGreaterEqual(len(data), 15)  # At least 15 trading days in a month
    
    def test_data_normalization(self):
        """Test that data normalization works correctly."""
        # Create sample data
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        data = pd.DataFrame({
            'open': range(len(dates)),
            'high': [x + 1 for x in range(len(dates))],
            'low': [x - 1 for x in range(len(dates))],
            'close': [x + 0.5 for x in range(len(dates))],
            'volume': [1000 * x for x in range(len(dates))]
        }, index=dates)
        
        # Normalize the data
        normalized = normalize_data(data)
        
        # Check that the normalized data has the expected columns
        expected_columns = ['open', 'high', 'low', 'close', 'volume', 'returns']
        for col in expected_columns:
            self.assertIn(col, normalized.columns)
        
        # Check that returns are calculated correctly
        # Returns should be (close_today - close_yesterday) / close_yesterday
        for i in range(1, len(normalized)):
            expected_return = (normalized['close'].iloc[i] - normalized['close'].iloc[i-1]) / normalized['close'].iloc[i-1]
            self.assertAlmostEqual(normalized['returns'].iloc[i], expected_return)
    
    def test_add_technical_indicators(self):
        """Test that adding technical indicators works correctly."""
        # Fetch some real data to test with
        data = self.yahoo_fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=(self.end_date - timedelta(days=100)).strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval=self.interval
        )
        
        # Add technical indicators
        data_with_indicators = add_technical_indicators(data)
        
        # Check that the data has the expected indicators
        expected_indicators = ['sma_20', 'sma_50', 'ema_12', 'ema_26', 'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_middle', 'bb_lower']
        for indicator in expected_indicators:
            self.assertIn(indicator, data_with_indicators.columns)
        
        # Check that the indicators have reasonable values
        # SMA should be the average of the last n closing prices
        for i in range(20, len(data_with_indicators)):
            expected_sma20 = data_with_indicators['close'].iloc[i-20:i].mean()
            self.assertAlmostEqual(data_with_indicators['sma_20'].iloc[i], expected_sma20, places=4)
        
        # RSI should be between 0 and 100
        self.assertTrue((data_with_indicators['rsi_14'].dropna() >= 0).all())
        self.assertTrue((data_with_indicators['rsi_14'].dropna() <= 100).all())
        
        # Bollinger Bands: Upper should be higher than middle, middle should be higher than lower
        self.assertTrue((data_with_indicators['bb_upper'].dropna() >= data_with_indicators['bb_middle'].dropna()).all())
        self.assertTrue((data_with_indicators['bb_middle'].dropna() >= data_with_indicators['bb_lower'].dropna()).all())

if __name__ == '__main__':
    unittest.main()
