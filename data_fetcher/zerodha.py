"""
Zerodha data fetcher for algorithmic trading system.
This module provides functionality to fetch historical and real-time market data from Zerodha.
"""

import pandas as pd
import datetime
import os
import logging
from kiteconnect import KiteConnect
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zerodha_fetcher')

class ZerodhaFetcher:
    """
    A class to fetch historical and real-time market data from Zerodha.
    """
    
    def __init__(self, api_key=None, access_token=None, cache_dir=None):
        """
        Initialize the Zerodha data fetcher.
        
        Parameters:
        -----------
        api_key : str, optional
            Zerodha API key. If None, it will try to load from config file.
        access_token : str, optional
            Zerodha access token. If None, it will try to load from config file.
        cache_dir : str, optional
            Directory to cache downloaded data. If None, no caching is performed.
        """
        self.api_key = api_key
        self.access_token = access_token
        self.cache_dir = cache_dir
        self.kite = None
        
        # Create cache directory if it doesn't exist
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            logger.info(f"Created cache directory: {cache_dir}")
        
        # Initialize Kite Connect if credentials are provided
        if api_key and access_token:
            self.initialize_kite()
    
    def initialize_kite(self):
        """
        Initialize the Kite Connect client.
        
        Returns:
        --------
        bool
            True if initialization was successful, False otherwise.
        """
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            logger.info("Kite Connect initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Kite Connect: {str(e)}")
            return False
    
    def load_credentials(self, config_file):
        """
        Load API credentials from a config file.
        
        Parameters:
        -----------
        config_file : str
            Path to the config file containing API credentials.
            
        Returns:
        --------
        bool
            True if credentials were loaded successfully, False otherwise.
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.api_key = config.get('api_key')
            self.access_token = config.get('access_token')
            
            if not self.api_key or not self.access_token:
                logger.error("API key or access token not found in config file")
                return False
            
            return self.initialize_kite()
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return False
    
    def fetch_historical_data(self, instrument_token, from_date, to_date=None, interval='day', continuous=False, oi=False):
        """
        Fetch historical OHLCV data for a given instrument token.
        
        Parameters:
        -----------
        instrument_token : int
            The instrument token for which to fetch data.
        from_date : str or datetime
            Start date for historical data in 'YYYY-MM-DD' format or as datetime object.
        to_date : str or datetime, optional
            End date for historical data in 'YYYY-MM-DD' format or as datetime object.
            If None, current date is used.
        interval : str, optional
            Data interval. Options: 'minute', '3minute', '5minute', '10minute', '15minute', '30minute', '60minute', 'day'
        continuous : bool, optional
            Whether to fetch continuous data for futures and options.
        oi : bool, optional
            Whether to fetch open interest data.
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame containing the historical OHLCV data.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Call initialize_kite() first.")
            return pd.DataFrame()
        
        # Convert string dates to datetime if necessary
        if isinstance(from_date, str):
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        
        if to_date is None:
            to_date = datetime.datetime.now()
        elif isinstance(to_date, str):
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
        
        # Check if data is in cache
        if self.cache_dir:
            cache_file = os.path.join(
                self.cache_dir, 
                f"zerodha_{instrument_token}_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}_{interval}.csv"
            )
            if os.path.exists(cache_file):
                logger.info(f"Loading cached data for instrument {instrument_token} from {cache_file}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # Fetch data from Zerodha
        logger.info(f"Fetching data for instrument {instrument_token} from {from_date} to {to_date} with interval {interval}")
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            if not df.empty:
                # Set date as index
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # Save to cache if enabled
                if self.cache_dir:
                    df.to_csv(cache_file)
                    logger.info(f"Cached data for instrument {instrument_token} to {cache_file}")
            
            return df
        except Exception as e:
            logger.error(f"Error fetching data for instrument {instrument_token}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_instruments(self, exchange=None):
        """
        Fetch the list of instruments available for trading.
        
        Parameters:
        -----------
        exchange : str, optional
            Filter instruments by exchange. If None, all instruments are returned.
            
        Returns:
        --------
        list
            List of instrument dictionaries.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Call initialize_kite() first.")
            return []
        
        try:
            instruments = self.kite.instruments(exchange=exchange)
            logger.info(f"Fetched {len(instruments)} instruments" + (f" for exchange {exchange}" if exchange else ""))
            return instruments
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            return []
    
    def get_instrument_token(self, symbol, exchange="NSE"):
        """
        Get the instrument token for a given symbol and exchange.
        
        Parameters:
        -----------
        symbol : str
            Trading symbol.
        exchange : str, optional
            Exchange name. Default is "NSE".
            
        Returns:
        --------
        int or None
            Instrument token if found, None otherwise.
        """
        instruments = self.fetch_instruments(exchange)
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol:
                return instrument['instrument_token']
        
        logger.error(f"Instrument token not found for {symbol} on {exchange}")
        return None
    
    def get_ltp(self, instrument_token):
        """
        Get the last traded price for a given instrument token.
        
        Parameters:
        -----------
        instrument_token : int
            The instrument token for which to fetch the LTP.
            
        Returns:
        --------
        float or None
            Last traded price if successful, None otherwise.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Call initialize_kite() first.")
            return None
        
        try:
            ltp = self.kite.ltp(instrument_token)[str(instrument_token)]['last_price']
            return ltp
        except Exception as e:
            logger.error(f"Error fetching LTP for instrument {instrument_token}: {str(e)}")
            return None
