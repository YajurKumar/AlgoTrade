"""
Yahoo Finance data fetcher for algorithmic trading system.
This module provides functionality to fetch historical market data from Yahoo Finance.
"""

import pandas as pd
import yfinance as yf
import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('yahoo_finance_fetcher')

class YahooFinanceFetcher:
    """
    A class to fetch historical market data from Yahoo Finance.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the Yahoo Finance data fetcher.
        
        Parameters:
        -----------
        cache_dir : str, optional
            Directory to cache downloaded data. If None, no caching is performed.
        """
        self.cache_dir = cache_dir
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            logger.info(f"Created cache directory: {cache_dir}")
    
    def fetch_historical_data(self, symbol, start_date, end_date=None, interval='1d', auto_adjust=True):
        """
        Fetch historical OHLCV data for a given symbol.
        
        Parameters:
        -----------
        symbol : str
            The ticker symbol to fetch data for.
        start_date : str or datetime
            Start date for historical data in 'YYYY-MM-DD' format or as datetime object.
        end_date : str or datetime, optional
            End date for historical data in 'YYYY-MM-DD' format or as datetime object.
            If None, current date is used.
        interval : str, optional
            Data interval. Options: '1m', '2m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo'
            Note: Intraday data (minute intervals) is only available for the last 7 days.
        auto_adjust : bool, optional
            Adjust all OHLC automatically (True by default).
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing the historical OHLCV data.
        """
        # Convert string dates to datetime if necessary
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        
        if end_date is None:
            end_date = datetime.datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        
        # Check if data is in cache
        if self.cache_dir:
            cache_file = os.path.join(
                self.cache_dir, 
                f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{interval}.csv"
            )
            if os.path.exists(cache_file):
                logger.info(f"Loading cached data for {symbol} from {cache_file}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Fetch data from Yahoo Finance
        logger.info(f"Fetching data for {symbol} from {start_date} to {end_date} with interval {interval}")
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval, auto_adjust=auto_adjust)
            
            # Save to cache if enabled
            if self.cache_dir and not data.empty:
                data.to_csv(cache_file)
                logger.info(f"Cached data for {symbol} to {cache_file}")
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_multiple_symbols(self, symbols, start_date, end_date=None, interval='1d'):
        """
        Fetch historical data for multiple symbols.
        
        Parameters:
        -----------
        symbols : list
            List of ticker symbols to fetch data for.
        start_date : str or datetime
            Start date for historical data.
        end_date : str or datetime, optional
            End date for historical data. If None, current date is used.
        interval : str, optional
            Data interval.
            
        Returns:
        --------
        dict
            Dictionary with symbols as keys and DataFrames as values.
        """
        result = {}
        for symbol in symbols:
            data = self.fetch_historical_data(symbol, start_date, end_date, interval)
            if not data.empty:
                result[symbol] = data
        return result
    
    def download_data(self, symbols, start_date, end_date=None, interval='1d', group_by='column'):
        """
        Download data for multiple symbols at once using yfinance's download function.
        This is more efficient than fetching symbols individually.
        
        Parameters:
        -----------
        symbols : list or str
            List of ticker symbols or a single symbol.
        start_date : str or datetime
            Start date for historical data.
        end_date : str or datetime, optional
            End date for historical data. If None, current date is used.
        interval : str, optional
            Data interval.
        group_by : str, optional
            Group by 'column' (default) or 'ticker'.
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing the historical data for all symbols.
        """
        logger.info(f"Downloading data for {symbols} from {start_date} to {end_date}")
        try:
            data = yf.download(symbols, start=start_date, end=end_date, interval=interval, group_by=group_by)
            return data
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            return pd.DataFrame()
