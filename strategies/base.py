"""
Base classes for trading strategies.
This module provides the core components for implementing trading algorithms.
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
from abc import ABC, abstractmethod

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.base import Strategy

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('strategies')

class TechnicalIndicators:
    """
    Class containing technical indicator calculations.
    """
    
    @staticmethod
    def sma(prices, period):
        """
        Calculate Simple Moving Average.
        
        Parameters:
        -----------
        prices : numpy.ndarray or pandas.Series
            Array of prices.
        period : int
            The period for the moving average.
            
        Returns:
        --------
        numpy.ndarray
            Array of SMA values.
        """
        return pd.Series(prices).rolling(window=period).mean().values
    
    @staticmethod
    def ema(prices, period):
        """
        Calculate Exponential Moving Average.
        
        Parameters:
        -----------
        prices : numpy.ndarray or pandas.Series
            Array of prices.
        period : int
            The period for the moving average.
            
        Returns:
        --------
        numpy.ndarray
            Array of EMA values.
        """
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def rsi(prices, period=14):
        """
        Calculate Relative Strength Index.
        
        Parameters:
        -----------
        prices : numpy.ndarray or pandas.Series
            Array of prices.
        period : int, optional
            The period for the RSI calculation.
            
        Returns:
        --------
        numpy.ndarray
            Array of RSI values.
        """
        # Convert to pandas Series if it's not already
        price_series = pd.Series(prices)
        
        # Calculate price changes
        deltas = price_series.diff()
        
        # Calculate gains and losses
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.values
    
    @staticmethod
    def macd(prices, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate Moving Average Convergence Divergence.
        
        Parameters:
        -----------
        prices : numpy.ndarray or pandas.Series
            Array of prices.
        fast_period : int, optional
            The period for the fast EMA.
        slow_period : int, optional
            The period for the slow EMA.
        signal_period : int, optional
            The period for the signal line.
            
        Returns:
        --------
        tuple
            (macd_line, signal_line, histogram)
        """
        # Convert to pandas Series if it's not already
        price_series = pd.Series(prices)
        
        # Calculate fast and slow EMAs
        fast_ema = price_series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = price_series.ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    @staticmethod
    def bollinger_bands(prices, period=20, num_std=2.0):
        """
        Calculate Bollinger Bands.
        
        Parameters:
        -----------
        prices : numpy.ndarray or pandas.Series
            Array of prices.
        period : int, optional
            The period for the moving average.
        num_std : float, optional
            The number of standard deviations for the bands.
            
        Returns:
        --------
        tuple
            (middle_band, upper_band, lower_band)
        """
        # Convert to pandas Series if it's not already
        price_series = pd.Series(prices)
        
        # Calculate middle band (simple moving average)
        middle_band = price_series.rolling(window=period).mean()
        
        # Calculate standard deviation
        std_dev = price_series.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return middle_band.values, upper_band.values, lower_band.values
    
    @staticmethod
    def atr(high, low, close, period=14):
        """
        Calculate Average True Range.
        
        Parameters:
        -----------
        high : numpy.ndarray or pandas.Series
            Array of high prices.
        low : numpy.ndarray or pandas.Series
            Array of low prices.
        close : numpy.ndarray or pandas.Series
            Array of close prices.
        period : int, optional
            The period for the ATR calculation.
            
        Returns:
        --------
        numpy.ndarray
            Array of ATR values.
        """
        # Convert to pandas Series if they're not already
        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)
        
        # Calculate true range
        prev_close = close_series.shift(1)
        tr1 = high_series - low_series
        tr2 = abs(high_series - prev_close)
        tr3 = abs(low_series - prev_close)
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=period).mean()
        
        return atr.values
    
    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3):
        """
        Calculate Stochastic Oscillator.
        
        Parameters:
        -----------
        high : numpy.ndarray or pandas.Series
            Array of high prices.
        low : numpy.ndarray or pandas.Series
            Array of low prices.
        close : numpy.ndarray or pandas.Series
            Array of close prices.
        k_period : int, optional
            The period for the %K line.
        d_period : int, optional
            The period for the %D line.
            
        Returns:
        --------
        tuple
            (%K, %D)
        """
        # Convert to pandas Series if they're not already
        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)
        
        # Calculate %K
        lowest_low = low_series.rolling(window=k_period).min()
        highest_high = high_series.rolling(window=k_period).max()
        k = 100 * ((close_series - lowest_low) / (highest_high - lowest_low))
        
        # Calculate %D
        d = k.rolling(window=d_period).mean()
        
        return k.values, d.values
    
    @staticmethod
    def adx(high, low, close, period=14):
        """
        Calculate Average Directional Index.
        
        Parameters:
        -----------
        high : numpy.ndarray or pandas.Series
            Array of high prices.
        low : numpy.ndarray or pandas.Series
            Array of low prices.
        close : numpy.ndarray or pandas.Series
            Array of close prices.
        period : int, optional
            The period for the ADX calculation.
            
        Returns:
        --------
        tuple
            (ADX, +DI, -DI)
        """
        # Convert to pandas Series if they're not already
        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)
        
        # Calculate +DM and -DM
        high_diff = high_series.diff()
        low_diff = low_series.diff()
        
        plus_dm = high_diff.copy()
        plus_dm[plus_dm < 0] = 0
        plus_dm[(high_diff <= 0) | (high_diff < low_diff.abs())] = 0
        
        minus_dm = low_diff.abs().copy()
        minus_dm[minus_dm < 0] = 0
        minus_dm[(low_diff >= 0) | (low_diff.abs() < high_diff)] = 0
        
        # Calculate ATR
        atr = TechnicalIndicators.atr(high, low, close, period)
        
        # Calculate +DI and -DI
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / pd.Series(atr)
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / pd.Series(atr)
        
        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calculate ADX
        adx = pd.Series(dx).rolling(window=period).mean()
        
        return adx.values, plus_di.values, minus_di.values


class AdvancedStrategy(Strategy):
    """
    Base class for advanced trading strategies.
    Extends the Strategy class with additional functionality.
    """
    
    def __init__(self, name=None):
        """
        Initialize a new advanced strategy.
        
        Parameters:
        -----------
        name : str, optional
            The name of the strategy.
        """
        super().__init__(name=name)
        self.indicators = TechnicalIndicators()
        self.risk_per_trade = 0.02  # Default risk per trade (2% of equity)
    
    def set_risk_per_trade(self, risk):
        """
        Set the risk per trade as a percentage of equity.
        
        Parameters:
        -----------
        risk : float
            The risk per trade as a percentage of equity (0.01 = 1%).
        """
        self.risk_per_trade = risk
    
    def calculate_position_size(self, entry_price, stop_loss, risk_amount=None):
        """
        Calculate the position size based on risk management rules.
        
        Parameters:
        -----------
        entry_price : float
            The entry price.
        stop_loss : float
            The stop loss price.
        risk_amount : float, optional
            The amount to risk. If None, uses risk_per_trade * equity.
            
        Returns:
        --------
        float
            The position size.
        """
        if risk_amount is None:
            risk_amount = self.equity * self.risk_per_trade
        
        # Calculate the risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        # Calculate the position size
        if risk_per_share > 0:
            position_size = risk_amount / risk_per_share
        else:
            position_size = 0
        
        return position_size
    
    def trailing_stop(self, position, current_price, trail_percent=0.02):
        """
        Update the stop loss of a position using a trailing stop.
        
        Parameters:
        -----------
        position : Position
            The position to update.
        current_price : float
            The current price.
        trail_percent : float, optional
            The trailing stop percentage.
            
        Returns:
        --------
        float
            The new stop loss price.
        """
        if position.direction == 'long':
            # For long positions, stop loss moves up as price increases
            new_stop = current_price * (1 - trail_percent)
            if position.stop_loss is None or new_stop > position.stop_loss:
                position.stop_loss = new_stop
        else:  # short
            # For short positions, stop loss moves down as price decreases
            new_stop = current_price * (1 + trail_percent)
            if position.stop_loss is None or new_stop < position.stop_loss:
                position.stop_loss = new_stop
        
        return position.stop_loss
