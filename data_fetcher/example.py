"""
Example script to demonstrate the usage of the data fetcher module.
This script shows how to fetch historical data from Yahoo Finance and Zerodha,
and how to normalize and preprocess the data for backtesting.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the data_fetcher module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from data_fetcher.normalizer import prepare_data_for_backtesting

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
    print("\nRaw data sample:")
    print(data.head())
    
    # Prepare data for backtesting
    prepared_data = prepare_data_for_backtesting(data)
    
    print("\nPrepared data sample (with technical indicators):")
    print(prepared_data.head())
    
    # Plot the data
    plt.figure(figsize=(12, 8))
    
    # Plot price and moving averages
    plt.subplot(2, 1, 1)
    plt.plot(prepared_data.index, prepared_data['close'], label='Close Price')
    plt.plot(prepared_data.index, prepared_data['sma_20'], label='SMA 20')
    plt.plot(prepared_data.index, prepared_data['sma_50'], label='SMA 50')
    plt.plot(prepared_data.index, prepared_data['bollinger_upper_20'], 'r--', label='Bollinger Upper')
    plt.plot(prepared_data.index, prepared_data['bollinger_lower_20'], 'r--', label='Bollinger Lower')
    plt.title(f'{symbol} Price and Indicators')
    plt.legend()
    plt.grid(True)
    
    # Plot RSI
    plt.subplot(2, 1, 2)
    plt.plot(prepared_data.index, prepared_data['rsi_14'], label='RSI 14')
    plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
    plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
    plt.title('RSI Indicator')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    
    # Save the plot
    plot_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', f'{symbol}_analysis.png')
    plt.savefig(plot_file)
    print(f"\nPlot saved to {plot_file}")
    
    # Save the data
    csv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', f'{symbol}_data.csv')
    prepared_data.to_csv(csv_file)
    print(f"Data saved to {csv_file}")
    
    print("\nNote: To use Zerodha data fetcher, you need to provide API credentials:")
    print("zerodha_fetcher = factory.get_zerodha_fetcher(api_key='your_api_key', access_token='your_access_token')")
    print("Or load from a config file:")
    print("zerodha_fetcher = factory.get_zerodha_fetcher(config_file='path/to/config.json')")

if __name__ == "__main__":
    main()
