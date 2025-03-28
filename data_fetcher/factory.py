"""
Data fetcher factory for algorithmic trading system.
This module provides a unified interface to fetch data from different sources.
"""

import logging
import os
from .yahoo_finance import YahooFinanceFetcher
from .zerodha import ZerodhaFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_fetcher')

class DataFetcherFactory:
    """
    Factory class to create and manage data fetchers from different sources.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the data fetcher factory.
        
        Parameters:
        -----------
        cache_dir : str, optional
            Directory to cache downloaded data. If None, a default directory is used.
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cache')
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            logger.info(f"Created cache directory: {cache_dir}")
        
        self.cache_dir = cache_dir
        self.yahoo_fetcher = None
        self.zerodha_fetcher = None
    
    def get_yahoo_fetcher(self):
        """
        Get or create a Yahoo Finance data fetcher.
        
        Returns:
        --------
        YahooFinanceFetcher
            An instance of the Yahoo Finance data fetcher.
        """
        if self.yahoo_fetcher is None:
            self.yahoo_fetcher = YahooFinanceFetcher(cache_dir=self.cache_dir)
            logger.info("Created Yahoo Finance data fetcher")
        
        return self.yahoo_fetcher
    
    def get_zerodha_fetcher(self, api_key=None, access_token=None, config_file=None):
        """
        Get or create a Zerodha data fetcher.
        
        Parameters:
        -----------
        api_key : str, optional
            Zerodha API key.
        access_token : str, optional
            Zerodha access token.
        config_file : str, optional
            Path to a config file containing API credentials.
            
        Returns:
        --------
        ZerodhaFetcher
            An instance of the Zerodha data fetcher.
        """
        if self.zerodha_fetcher is None:
            self.zerodha_fetcher = ZerodhaFetcher(
                api_key=api_key,
                access_token=access_token,
                cache_dir=self.cache_dir
            )
            logger.info("Created Zerodha data fetcher")
        
        # Load credentials from config file if provided
        if config_file and not (api_key and access_token):
            self.zerodha_fetcher.load_credentials(config_file)
        
        return self.zerodha_fetcher
    
    def fetch_historical_data(self, symbol, start_date, end_date=None, interval='1d', source='yahoo'):
        """
        Fetch historical data for a symbol from the specified source.
        
        Parameters:
        -----------
        symbol : str
            The symbol to fetch data for.
        start_date : str or datetime
            Start date for historical data.
        end_date : str or datetime, optional
            End date for historical data. If None, current date is used.
        interval : str, optional
            Data interval. Format depends on the source.
        source : str, optional
            Data source. Options: 'yahoo', 'zerodha'
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing the historical data.
        """
        if source.lower() == 'yahoo':
            fetcher = self.get_yahoo_fetcher()
            return fetcher.fetch_historical_data(symbol, start_date, end_date, interval)
        
        elif source.lower() == 'zerodha':
            if self.zerodha_fetcher is None:
                logger.error("Zerodha fetcher not initialized. Call get_zerodha_fetcher() first.")
                return None
            
            # Convert Yahoo Finance interval format to Zerodha format
            interval_mapping = {
                '1m': 'minute',
                '3m': '3minute',
                '5m': '5minute',
                '15m': '15minute',
                '30m': '30minute',
                '60m': '60minute',
                '1h': '60minute',
                '1d': 'day',
                'day': 'day'
            }
            
            zerodha_interval = interval_mapping.get(interval, 'day')
            
            # Get instrument token for the symbol
            instrument_token = self.zerodha_fetcher.get_instrument_token(symbol)
            if instrument_token:
                return self.zerodha_fetcher.fetch_historical_data(
                    instrument_token=instrument_token,
                    from_date=start_date,
                    to_date=end_date,
                    interval=zerodha_interval
                )
            else:
                logger.error(f"Instrument token not found for {symbol}")
                return None
        
        else:
            logger.error(f"Unknown data source: {source}")
            return None
