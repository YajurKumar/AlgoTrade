"""
Market data module for Zerodha Kite Connect API.
This module provides functionality to fetch market data from Zerodha.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from kiteconnect.exceptions import DataException

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zerodha_market_data')

class MarketData:
    """
    Class to fetch market data from Zerodha's Kite Connect API.
    """
    
    def __init__(self, kite=None):
        """
        Initialize the market data fetcher.
        
        Parameters:
        -----------
        kite : KiteConnect, optional
            An authenticated KiteConnect instance.
        """
        self.kite = kite
    
    def set_kite(self, kite):
        """
        Set the KiteConnect instance.
        
        Parameters:
        -----------
        kite : KiteConnect
            An authenticated KiteConnect instance.
        """
        self.kite = kite
    
    def get_quote(self, symbols):
        """
        Get quotes for given symbols.
        
        Parameters:
        -----------
        symbols : str or list
            Trading symbol(s) with exchange prefix (e.g., 'NSE:RELIANCE').
            
        Returns:
        --------
        dict
            Dictionary of quotes.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return {}
        
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            
            quotes = self.kite.quote(symbols)
            logger.info(f"Got quotes for {len(symbols)} symbols")
            return quotes
        
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            return {}
    
    def get_ohlc(self, symbols):
        """
        Get OHLC data for given symbols.
        
        Parameters:
        -----------
        symbols : str or list
            Trading symbol(s) with exchange prefix (e.g., 'NSE:RELIANCE').
            
        Returns:
        --------
        dict
            Dictionary of OHLC data.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return {}
        
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            
            ohlc = self.kite.ohlc(symbols)
            logger.info(f"Got OHLC data for {len(symbols)} symbols")
            return ohlc
        
        except Exception as e:
            logger.error(f"Error getting OHLC data: {str(e)}")
            return {}
    
    def get_ltp(self, symbols):
        """
        Get last traded price for given symbols.
        
        Parameters:
        -----------
        symbols : str or list
            Trading symbol(s) with exchange prefix (e.g., 'NSE:RELIANCE').
            
        Returns:
        --------
        dict
            Dictionary of last traded prices.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return {}
        
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            
            ltp = self.kite.ltp(symbols)
            logger.info(f"Got LTP for {len(symbols)} symbols")
            return ltp
        
        except Exception as e:
            logger.error(f"Error getting LTP: {str(e)}")
            return {}
    
    def get_historical_data(self, symbol, from_date, to_date, interval, continuous=False, oi=False):
        """
        Get historical data for a symbol.
        
        Parameters:
        -----------
        symbol : str
            Trading symbol with exchange prefix (e.g., 'NSE:RELIANCE').
        from_date : datetime
            From date.
        to_date : datetime
            To date.
        interval : str
            Candle interval ('minute', '3minute', '5minute', '10minute', '15minute', '30minute', 'hour', 'day', 'week').
        continuous : bool, optional
            Whether to fetch continuous data for futures and options.
        oi : bool, optional
            Whether to fetch open interest data.
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame of historical data.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return pd.DataFrame()
        
        try:
            # Split symbol into exchange and trading symbol
            if ':' in symbol:
                exchange, trading_symbol = symbol.split(':')
            else:
                logger.error(f"Symbol {symbol} must include exchange prefix (e.g., 'NSE:RELIANCE')")
                return pd.DataFrame()
            
            # Get instrument token
            instruments = self.kite.instruments(exchange)
            instrument_token = None
            
            for instrument in instruments:
                if instrument['tradingsymbol'] == trading_symbol:
                    instrument_token = instrument['instrument_token']
                    break
            
            if not instrument_token:
                logger.error(f"Instrument token not found for {symbol}")
                return pd.DataFrame()
            
            # Fetch historical data
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
            
            # Convert date column to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            
            logger.info(f"Got historical data for {symbol} from {from_date} to {to_date} ({len(df)} records)")
            return df
        
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return pd.DataFrame()
    
    def get_instruments(self, exchange=None):
        """
        Get instruments for a given exchange.
        
        Parameters:
        -----------
        exchange : str, optional
            Exchange (NSE, BSE, NFO, etc.). If None, gets all instruments.
            
        Returns:
        --------
        list
            List of instruments.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return []
        
        try:
            instruments = self.kite.instruments(exchange)
            logger.info(f"Got {len(instruments)} instruments for {exchange or 'all exchanges'}")
            return instruments
        
        except Exception as e:
            logger.error(f"Error getting instruments: {str(e)}")
            return []
    
    def search_instruments(self, exchange, query):
        """
        Search for instruments.
        
        Parameters:
        -----------
        exchange : str
            Exchange (NSE, BSE, NFO, etc.).
        query : str
            Search query.
            
        Returns:
        --------
        list
            List of matching instruments.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return []
        
        try:
            instruments = self.kite.instruments(exchange)
            
            # Filter instruments by query
            matches = []
            query = query.upper()
            
            for instrument in instruments:
                if query in instrument['tradingsymbol'].upper() or query in instrument.get('name', '').upper():
                    matches.append(instrument)
            
            logger.info(f"Found {len(matches)} instruments matching '{query}' on {exchange}")
            return matches
        
        except Exception as e:
            logger.error(f"Error searching instruments: {str(e)}")
            return []
    
    def get_margins(self):
        """
        Get user margins.
        
        Returns:
        --------
        dict
            Dictionary of margins.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return {}
        
        try:
            margins = self.kite.margins()
            logger.info("Got user margins")
            return margins
        
        except Exception as e:
            logger.error(f"Error getting margins: {str(e)}")
            return {}
    
    def get_positions(self):
        """
        Get user positions.
        
        Returns:
        --------
        dict
            Dictionary of positions.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return {}
        
        try:
            positions = self.kite.positions()
            logger.info("Got user positions")
            return positions
        
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return {}
    
    def get_holdings(self):
        """
        Get user holdings.
        
        Returns:
        --------
        list
            List of holdings.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return []
        
        try:
            holdings = self.kite.holdings()
            logger.info("Got user holdings")
            return holdings
        
        except Exception as e:
            logger.error(f"Error getting holdings: {str(e)}")
            return []
