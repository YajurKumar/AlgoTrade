"""
Example script to demonstrate the usage of the backtesting framework.
This script shows how to backtest a trading strategy using historical data.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from data_fetcher.normalizer import prepare_data_for_backtesting
from backtesting.base import Backtester
from backtesting.strategies import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy

def main():
    # Create a data fetcher factory
    factory = DataFetcherFactory()
    
    # Get a Yahoo Finance data fetcher
    yahoo_fetcher = factory.get_yahoo_fetcher()
    
    # Fetch historical data for a stock
    symbol = 'RELIANCE.NS'  # Reliance Industries on NSE
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
    data = yahoo_fetcher.fetch_historical_data(symbol, start_date, end_date, interval='1d')
    
    if data.empty:
        print("No data fetched. Please check the symbol and date range.")
        return
    
    print(f"Fetched {len(data)} data points")
    
    # Prepare data for backtesting
    prepared_data = prepare_data_for_backtesting(data)
    
    # Create output directory for results
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Test different strategies
    strategies = [
        MovingAverageCrossover(symbol, fast_period=20, slow_period=50, position_size=0.95),
        RSIStrategy(symbol, rsi_period=14, oversold=30, overbought=70, position_size=0.95),
        BollingerBandsStrategy(symbol, period=20, num_std=2.0, position_size=0.95)
    ]
    
    for strategy in strategies:
        print(f"\nBacktesting {strategy.name} strategy...")
        
        # Create a backtester
        backtester = Backtester(
            strategy=strategy,
            data={symbol: prepared_data},
            initial_capital=100000.0,
            commission=0.1  # 0.1% commission per trade
        )
        
        # Run the backtest
        results = backtester.run()
        
        # Print performance metrics
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Annual Return: {results['annual_return']:.2%}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Win Rate: {results['win_rate']:.2%}")
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Number of Trades: {results['num_trades']}")
        
        # Plot results
        plot_path = os.path.join(output_dir, f"{symbol}_{strategy.name}_backtest.png")
        backtester.plot_results(save_path=plot_path)
        print(f"Plot saved to {plot_path}")
        
        # Save detailed results to CSV
        csv_path = os.path.join(output_dir, f"{symbol}_{strategy.name}_results.csv")
        results['equity_curve'].to_csv(csv_path)
        print(f"Results saved to {csv_path}")

if __name__ == "__main__":
    main()
