"""
Example trading strategies for the backtesting framework.
This module provides sample strategy implementations that can be used with the backtesting system.
"""

import pandas as pd
import numpy as np
import logging
from .base import Strategy

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('strategies')

class MovingAverageCrossover(Strategy):
    """
    Moving Average Crossover strategy.
    
    This strategy generates buy signals when the fast moving average crosses above
    the slow moving average, and sell signals when the fast moving average crosses
    below the slow moving average.
    """
    
    def __init__(self, symbol, fast_period=20, slow_period=50, position_size=1.0):
        """
        Initialize the Moving Average Crossover strategy.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        fast_period : int, optional
            The period for the fast moving average.
        slow_period : int, optional
            The period for the slow moving average.
        position_size : float, optional
            The position size as a fraction of available capital.
        """
        super().__init__(name=f"MA_Cross_{fast_period}_{slow_period}")
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.position_size = position_size
        self.in_position = False
    
    def initialize(self):
        """
        Initialize the strategy.
        """
        logger.info(f"Initializing {self.name} strategy for {self.symbol}")
        logger.info(f"Fast period: {self.fast_period}, Slow period: {self.slow_period}")
    
    def next(self, data):
        """
        Process the next data point.
        
        Parameters:
        -----------
        data : dict
            Dictionary mapping symbols to current data.
        """
        if self.symbol not in data:
            return
        
        current_data = data[self.symbol]
        
        # Skip if we don't have enough data for the slow moving average
        if self.current_index < self.slow_period:
            return
        
        # Calculate moving averages
        prices = self.data[self.symbol]['close'].values
        fast_ma = np.mean(prices[self.current_index - self.fast_period + 1:self.current_index + 1])
        slow_ma = np.mean(prices[self.current_index - self.slow_period + 1:self.current_index + 1])
        
        # Previous moving averages
        if self.current_index > self.slow_period:
            prev_prices = self.data[self.symbol]['close'].values
            prev_fast_ma = np.mean(prev_prices[self.current_index - self.fast_period:self.current_index])
            prev_slow_ma = np.mean(prev_prices[self.current_index - self.slow_period:self.current_index])
        else:
            prev_fast_ma = fast_ma
            prev_slow_ma = slow_ma
        
        # Check for crossover
        current_price = current_data['close']
        
        # Buy signal: fast MA crosses above slow MA
        if fast_ma > slow_ma and prev_fast_ma <= prev_slow_ma and not self.in_position:
            # Calculate position size
            position_value = self.cash * self.position_size
            quantity = position_value / current_price
            
            logger.info(f"{self.current_time}: BUY {self.symbol} @ {current_price:.2f}")
            self.buy(self.symbol, quantity)
            self.in_position = True
        
        # Sell signal: fast MA crosses below slow MA
        elif fast_ma < slow_ma and prev_fast_ma >= prev_slow_ma and self.in_position:
            # Close all open positions for this symbol
            for position in self.get_open_positions(self.symbol):
                logger.info(f"{self.current_time}: SELL {self.symbol} @ {current_price:.2f}")
                self.close_position(position)
            
            self.in_position = False


class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) strategy.
    
    This strategy generates buy signals when the RSI falls below the oversold level
    and then rises back above it, and sell signals when the RSI rises above the
    overbought level and then falls back below it.
    """
    
    def __init__(self, symbol, rsi_period=14, oversold=30, overbought=70, position_size=1.0):
        """
        Initialize the RSI strategy.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        rsi_period : int, optional
            The period for the RSI calculation.
        oversold : int, optional
            The oversold level.
        overbought : int, optional
            The overbought level.
        position_size : float, optional
            The position size as a fraction of available capital.
        """
        super().__init__(name=f"RSI_{rsi_period}_{oversold}_{overbought}")
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.position_size = position_size
        self.in_position = False
        self.was_oversold = False
        self.was_overbought = False
    
    def initialize(self):
        """
        Initialize the strategy.
        """
        logger.info(f"Initializing {self.name} strategy for {self.symbol}")
        logger.info(f"RSI period: {self.rsi_period}, Oversold: {self.oversold}, Overbought: {self.overbought}")
    
    def calculate_rsi(self, prices, period=14):
        """
        Calculate the Relative Strength Index.
        
        Parameters:
        -----------
        prices : numpy.ndarray
            Array of prices.
        period : int, optional
            The period for the RSI calculation.
            
        Returns:
        --------
        float
            The RSI value.
        """
        if len(prices) <= period:
            return 50  # Default value if not enough data
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Calculate gains and losses
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def next(self, data):
        """
        Process the next data point.
        
        Parameters:
        -----------
        data : dict
            Dictionary mapping symbols to current data.
        """
        if self.symbol not in data:
            return
        
        current_data = data[self.symbol]
        
        # Skip if we don't have enough data for the RSI
        if self.current_index < self.rsi_period + 1:
            return
        
        # Calculate RSI
        prices = self.data[self.symbol]['close'].values[:self.current_index + 1]
        rsi = self.calculate_rsi(prices, self.rsi_period)
        
        # Current price
        current_price = current_data['close']
        
        # Check for buy signal: RSI was below oversold and is now rising above it
        if rsi <= self.oversold:
            self.was_oversold = True
        
        if rsi > self.oversold and self.was_oversold and not self.in_position:
            # Calculate position size
            position_value = self.cash * self.position_size
            quantity = position_value / current_price
            
            logger.info(f"{self.current_time}: BUY {self.symbol} @ {current_price:.2f} (RSI: {rsi:.2f})")
            self.buy(self.symbol, quantity)
            self.in_position = True
            self.was_oversold = False
        
        # Check for sell signal: RSI was above overbought and is now falling below it
        if rsi >= self.overbought:
            self.was_overbought = True
        
        if rsi < self.overbought and self.was_overbought and self.in_position:
            # Close all open positions for this symbol
            for position in self.get_open_positions(self.symbol):
                logger.info(f"{self.current_time}: SELL {self.symbol} @ {current_price:.2f} (RSI: {rsi:.2f})")
                self.close_position(position)
            
            self.in_position = False
            self.was_overbought = False


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands strategy.
    
    This strategy generates buy signals when the price touches the lower band
    and sell signals when the price touches the upper band.
    """
    
    def __init__(self, symbol, period=20, num_std=2.0, position_size=1.0):
        """
        Initialize the Bollinger Bands strategy.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        period : int, optional
            The period for the moving average.
        num_std : float, optional
            The number of standard deviations for the bands.
        position_size : float, optional
            The position size as a fraction of available capital.
        """
        super().__init__(name=f"BB_{period}_{num_std}")
        self.symbol = symbol
        self.period = period
        self.num_std = num_std
        self.position_size = position_size
        self.in_position = False
    
    def initialize(self):
        """
        Initialize the strategy.
        """
        logger.info(f"Initializing {self.name} strategy for {self.symbol}")
        logger.info(f"Period: {self.period}, Std Dev: {self.num_std}")
    
    def calculate_bollinger_bands(self, prices, period=20, num_std=2.0):
        """
        Calculate Bollinger Bands.
        
        Parameters:
        -----------
        prices : numpy.ndarray
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
        if len(prices) < period:
            return None, None, None
        
        # Calculate middle band (simple moving average)
        middle_band = np.mean(prices[-period:])
        
        # Calculate standard deviation
        std_dev = np.std(prices[-period:])
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return middle_band, upper_band, lower_band
    
    def next(self, data):
        """
        Process the next data point.
        
        Parameters:
        -----------
        data : dict
            Dictionary mapping symbols to current data.
        """
        if self.symbol not in data:
            return
        
        current_data = data[self.symbol]
        
        # Skip if we don't have enough data for the Bollinger Bands
        if self.current_index < self.period:
            return
        
        # Calculate Bollinger Bands
        prices = self.data[self.symbol]['close'].values[:self.current_index + 1]
        middle_band, upper_band, lower_band = self.calculate_bollinger_bands(prices, self.period, self.num_std)
        
        if middle_band is None:
            return
        
        # Current price
        current_price = current_data['close']
        
        # Buy signal: price touches or crosses below the lower band
        if current_price <= lower_band and not self.in_position:
            # Calculate position size
            position_value = self.cash * self.position_size
            quantity = position_value / current_price
            
            logger.info(f"{self.current_time}: BUY {self.symbol} @ {current_price:.2f} (Lower Band: {lower_band:.2f})")
            self.buy(self.symbol, quantity)
            self.in_position = True
        
        # Sell signal: price touches or crosses above the upper band
        elif current_price >= upper_band and self.in_position:
            # Close all open positions for this symbol
            for position in self.get_open_positions(self.symbol):
                logger.info(f"{self.current_time}: SELL {self.symbol} @ {current_price:.2f} (Upper Band: {upper_band:.2f})")
                self.close_position(position)
            
            self.in_position = False
