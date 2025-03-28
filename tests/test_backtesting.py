"""
Unit tests for the backtesting framework.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.base import Strategy, Backtester, Position, Order
from data_fetcher.factory import DataFetcherFactory

class SimpleMovingAverageStrategy(Strategy):
    """A simple moving average crossover strategy for testing."""
    
    def __init__(self, symbol, fast_period=10, slow_period=30):
        """Initialize the strategy."""
        super().__init__(symbol)
        self.name = "SMA Crossover"
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data):
        """Generate trading signals based on SMA crossover."""
        # Calculate SMAs
        data['fast_sma'] = data['close'].rolling(window=self.fast_period).mean()
        data['slow_sma'] = data['close'].rolling(window=self.slow_period).mean()
        
        # Initialize signals
        data['signal'] = 0
        
        # Generate signals: 1 for buy, -1 for sell
        # Buy when fast SMA crosses above slow SMA
        # Sell when fast SMA crosses below slow SMA
        for i in range(1, len(data)):
            if (data['fast_sma'].iloc[i-1] <= data['slow_sma'].iloc[i-1] and 
                data['fast_sma'].iloc[i] > data['slow_sma'].iloc[i]):
                data.loc[data.index[i], 'signal'] = 1
            elif (data['fast_sma'].iloc[i-1] >= data['slow_sma'].iloc[i-1] and 
                  data['fast_sma'].iloc[i] < data['slow_sma'].iloc[i]):
                data.loc[data.index[i], 'signal'] = -1
        
        return data

class TestBacktesting(unittest.TestCase):
    """Test cases for the backtesting framework."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple strategy
        self.symbol = "AAPL"
        self.strategy = SimpleMovingAverageStrategy(symbol=self.symbol)
        
        # Create sample data
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=100)
        
        # Fetch real data for testing
        factory = DataFetcherFactory()
        fetcher = factory.get_yahoo_fetcher()
        self.data = fetcher.fetch_historical_data(
            symbol=self.symbol,
            start_date=self.start_date.strftime('%Y-%m-%d'),
            end_date=self.end_date.strftime('%Y-%m-%d'),
            interval="1d"
        )
        
        # Create a backtester
        self.backtester = Backtester(
            strategy=self.strategy,
            data={self.symbol: self.data},
            initial_capital=10000.0,
            commission=0.001
        )
    
    def test_position_management(self):
        """Test position creation and management."""
        # Create a position
        position = Position(
            symbol=self.symbol,
            entry_price=150.0,
            quantity=10,
            entry_time=datetime.now()
        )
        
        # Test position properties
        self.assertEqual(position.symbol, self.symbol)
        self.assertEqual(position.entry_price, 150.0)
        self.assertEqual(position.quantity, 10)
        self.assertEqual(position.value, 1500.0)
        
        # Test position update
        position.update_price(160.0)
        self.assertEqual(position.current_price, 160.0)
        self.assertEqual(position.unrealized_pnl, 100.0)
        self.assertEqual(position.unrealized_pnl_pct, 100.0 / 1500.0)
        
        # Test position close
        closed_pnl = position.close(160.0, datetime.now())
        self.assertEqual(closed_pnl, 100.0)
        self.assertTrue(position.is_closed)
    
    def test_order_execution(self):
        """Test order creation and execution."""
        # Create a buy order
        buy_order = Order(
            symbol=self.symbol,
            order_type="BUY",
            quantity=10,
            price=150.0,
            time=datetime.now()
        )
        
        # Test order properties
        self.assertEqual(buy_order.symbol, self.symbol)
        self.assertEqual(buy_order.order_type, "BUY")
        self.assertEqual(buy_order.quantity, 10)
        self.assertEqual(buy_order.price, 150.0)
        self.assertEqual(buy_order.value, 1500.0)
        
        # Create a sell order
        sell_order = Order(
            symbol=self.symbol,
            order_type="SELL",
            quantity=10,
            price=160.0,
            time=datetime.now()
        )
        
        # Test order properties
        self.assertEqual(sell_order.symbol, self.symbol)
        self.assertEqual(sell_order.order_type, "SELL")
        self.assertEqual(sell_order.quantity, 10)
        self.assertEqual(sell_order.price, 160.0)
        self.assertEqual(sell_order.value, 1600.0)
    
    def test_backtester_initialization(self):
        """Test backtester initialization."""
        self.assertEqual(self.backtester.initial_capital, 10000.0)
        self.assertEqual(self.backtester.current_capital, 10000.0)
        self.assertEqual(self.backtester.commission, 0.001)
        self.assertEqual(len(self.backtester.positions), 0)
        self.assertEqual(len(self.backtester.closed_positions), 0)
        self.assertEqual(len(self.backtester.orders), 0)
    
    def test_backtester_run(self):
        """Test running a backtest."""
        # Run the backtest
        results = self.backtester.run()
        
        # Check that results contain expected metrics
        expected_metrics = [
            'total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio',
            'win_rate', 'profit_factor', 'num_trades', 'final_equity'
        ]
        for metric in expected_metrics:
            self.assertIn(metric, results)
        
        # Check that equity curve is created
        self.assertIn('equity_curve', results)
        self.assertIsInstance(results['equity_curve'], pd.Series)
        
        # Check that the number of trades is reasonable
        # For a 100-day period with SMA crossover, we expect at least a few trades
        self.assertGreater(results['num_trades'], 0)
        
        # Check that final equity is different from initial capital (strategy did something)
        self.assertNotEqual(results['final_equity'], self.backtester.initial_capital)
    
    def test_performance_metrics(self):
        """Test calculation of performance metrics."""
        # Create a sample equity curve
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        equity = pd.Series(
            [10000 * (1 + 0.001) ** i for i in range(len(dates))],
            index=dates
        )
        
        # Calculate metrics
        metrics = self.backtester._calculate_performance_metrics(
            equity_curve=equity,
            trades=[
                {'entry_price': 100, 'exit_price': 110, 'pnl': 10, 'pnl_pct': 0.1},
                {'entry_price': 110, 'exit_price': 105, 'pnl': -5, 'pnl_pct': -0.045},
                {'entry_price': 105, 'exit_price': 115, 'pnl': 10, 'pnl_pct': 0.095}
            ]
        )
        
        # Check metrics
        self.assertGreater(metrics['total_return'], 0)
        self.assertGreater(metrics['annual_return'], 0)
        self.assertGreaterEqual(metrics['max_drawdown'], 0)
        self.assertEqual(metrics['num_trades'], 3)
        self.assertAlmostEqual(metrics['win_rate'], 2/3, places=4)
        self.assertGreater(metrics['profit_factor'], 1)  # Profitable strategy

if __name__ == '__main__':
    unittest.main()
