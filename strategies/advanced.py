"""
Advanced trading strategies for algorithmic trading.
This module provides sophisticated trading algorithms that can be used with the backtesting system.
"""

import pandas as pd
import numpy as np
import logging
import os
import sys

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import AdvancedStrategy, TechnicalIndicators

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('advanced_strategies')

class TrendFollowingStrategy(AdvancedStrategy):
    """
    Trend Following Strategy using multiple indicators to identify and follow trends.
    
    This strategy combines moving averages, ADX, and MACD to identify strong trends
    and enter positions in the direction of the trend with proper risk management.
    """
    
    def __init__(self, symbol, ema_short=20, ema_long=50, adx_period=14, adx_threshold=25, 
                 macd_fast=12, macd_slow=26, macd_signal=9, risk_per_trade=0.02, 
                 trailing_stop_pct=0.03):
        """
        Initialize the Trend Following Strategy.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        ema_short : int, optional
            The period for the short EMA.
        ema_long : int, optional
            The period for the long EMA.
        adx_period : int, optional
            The period for the ADX calculation.
        adx_threshold : float, optional
            The threshold for considering a trend strong.
        macd_fast : int, optional
            The period for the fast EMA in MACD.
        macd_slow : int, optional
            The period for the slow EMA in MACD.
        macd_signal : int, optional
            The period for the signal line in MACD.
        risk_per_trade : float, optional
            The risk per trade as a percentage of equity (0.02 = 2%).
        trailing_stop_pct : float, optional
            The trailing stop percentage (0.03 = 3%).
        """
        super().__init__(name=f"TrendFollow_EMA{ema_short}_{ema_long}_ADX{adx_period}")
        self.symbol = symbol
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.risk_per_trade = risk_per_trade
        self.trailing_stop_pct = trailing_stop_pct
        self.in_position = False
        self.trend_direction = None  # 'up', 'down', or None
    
    def initialize(self):
        """
        Initialize the strategy.
        """
        logger.info(f"Initializing {self.name} strategy for {self.symbol}")
        logger.info(f"EMA periods: {self.ema_short}/{self.ema_long}, ADX period: {self.adx_period}, threshold: {self.adx_threshold}")
        logger.info(f"MACD parameters: {self.macd_fast}/{self.macd_slow}/{self.macd_signal}")
        logger.info(f"Risk per trade: {self.risk_per_trade:.2%}, Trailing stop: {self.trailing_stop_pct:.2%}")
    
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
        
        # Skip if we don't have enough data
        min_periods = max(self.ema_long, self.adx_period, self.macd_slow + self.macd_signal)
        if self.current_index < min_periods:
            return
        
        # Get price data
        prices = self.data[self.symbol]['close'].values[:self.current_index + 1]
        highs = self.data[self.symbol]['high'].values[:self.current_index + 1]
        lows = self.data[self.symbol]['low'].values[:self.current_index + 1]
        
        # Calculate indicators
        ema_short = TechnicalIndicators.ema(prices, self.ema_short)
        ema_long = TechnicalIndicators.ema(prices, self.ema_long)
        
        adx, plus_di, minus_di = TechnicalIndicators.adx(highs, lows, prices, self.adx_period)
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(
            prices, self.macd_fast, self.macd_slow, self.macd_signal
        )
        
        # Current price
        current_price = current_data['close']
        
        # Determine trend direction
        if ema_short[-1] > ema_long[-1] and plus_di[-1] > minus_di[-1]:
            new_trend = 'up'
        elif ema_short[-1] < ema_long[-1] and plus_di[-1] < minus_di[-1]:
            new_trend = 'down'
        else:
            new_trend = None
        
        # Check for trend change
        trend_changed = new_trend != self.trend_direction
        self.trend_direction = new_trend
        
        # Check for strong trend
        strong_trend = adx[-1] > self.adx_threshold
        
        # Check for MACD signal
        macd_signal_bullish = histogram[-1] > 0 and histogram[-2] <= 0  # Crossed above zero
        macd_signal_bearish = histogram[-1] < 0 and histogram[-2] >= 0  # Crossed below zero
        
        # Update trailing stops for open positions
        for position in self.get_open_positions(self.symbol):
            self.trailing_stop(position, current_price, self.trailing_stop_pct)
        
        # Entry and exit logic
        if not self.in_position:
            # Entry conditions
            if strong_trend:
                if self.trend_direction == 'up' and macd_signal_bullish:
                    # Calculate stop loss based on recent swing low
                    stop_loss = min(lows[-20:])
                    
                    # Calculate position size based on risk
                    position_size = self.calculate_position_size(current_price, stop_loss)
                    
                    logger.info(f"{self.current_time}: BUY {self.symbol} @ {current_price:.2f} (Stop: {stop_loss:.2f})")
                    order = self.buy(self.symbol, position_size)
                    
                    # Set the stop loss for the position
                    if len(self.get_open_positions(self.symbol)) > 0:
                        position = self.get_open_positions(self.symbol)[0]
                        position.stop_loss = stop_loss
                    
                    self.in_position = True
                
                elif self.trend_direction == 'down' and macd_signal_bearish:
                    # Calculate stop loss based on recent swing high
                    stop_loss = max(highs[-20:])
                    
                    # Calculate position size based on risk
                    position_size = self.calculate_position_size(current_price, stop_loss)
                    
                    logger.info(f"{self.current_time}: SELL {self.symbol} @ {current_price:.2f} (Stop: {stop_loss:.2f})")
                    order = self.sell(self.symbol, position_size)
                    
                    # Set the stop loss for the position
                    if len(self.get_open_positions(self.symbol)) > 0:
                        position = self.get_open_positions(self.symbol)[0]
                        position.stop_loss = stop_loss
                    
                    self.in_position = True
        
        else:  # In position
            # Exit conditions
            positions = self.get_open_positions(self.symbol)
            if positions:
                position = positions[0]
                
                # Exit if trend changes direction
                if (position.direction == 'long' and self.trend_direction == 'down') or \
                   (position.direction == 'short' and self.trend_direction == 'up'):
                    logger.info(f"{self.current_time}: EXIT {self.symbol} @ {current_price:.2f} (Trend change)")
                    self.close_position(position)
                    self.in_position = False


class MeanReversionStrategy(AdvancedStrategy):
    """
    Mean Reversion Strategy using Bollinger Bands and RSI.
    
    This strategy looks for overbought/oversold conditions using Bollinger Bands
    and RSI, and enters positions expecting the price to revert to the mean.
    """
    
    def __init__(self, symbol, bb_period=20, bb_std=2.0, rsi_period=14, 
                 rsi_oversold=30, rsi_overbought=70, risk_per_trade=0.01,
                 take_profit_atr_multiple=2.0, stop_loss_atr_multiple=1.0,
                 atr_period=14):
        """
        Initialize the Mean Reversion Strategy.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        bb_period : int, optional
            The period for Bollinger Bands calculation.
        bb_std : float, optional
            The number of standard deviations for Bollinger Bands.
        rsi_period : int, optional
            The period for RSI calculation.
        rsi_oversold : int, optional
            The RSI level considered oversold.
        rsi_overbought : int, optional
            The RSI level considered overbought.
        risk_per_trade : float, optional
            The risk per trade as a percentage of equity (0.01 = 1%).
        take_profit_atr_multiple : float, optional
            The take profit level as a multiple of ATR.
        stop_loss_atr_multiple : float, optional
            The stop loss level as a multiple of ATR.
        atr_period : int, optional
            The period for ATR calculation.
        """
        super().__init__(name=f"MeanReversion_BB{bb_period}_RSI{rsi_period}")
        self.symbol = symbol
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.risk_per_trade = risk_per_trade
        self.take_profit_atr_multiple = take_profit_atr_multiple
        self.stop_loss_atr_multiple = stop_loss_atr_multiple
        self.atr_period = atr_period
        self.in_position = False
    
    def initialize(self):
        """
        Initialize the strategy.
        """
        logger.info(f"Initializing {self.name} strategy for {self.symbol}")
        logger.info(f"Bollinger Bands: period={self.bb_period}, std={self.bb_std}")
        logger.info(f"RSI: period={self.rsi_period}, oversold={self.rsi_oversold}, overbought={self.rsi_overbought}")
        logger.info(f"Risk per trade: {self.risk_per_trade:.2%}")
        logger.info(f"Take profit: {self.take_profit_atr_multiple}x ATR, Stop loss: {self.stop_loss_atr_multiple}x ATR")
    
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
        
        # Skip if we don't have enough data
        min_periods = max(self.bb_period, self.rsi_period, self.atr_period)
        if self.current_index < min_periods:
            return
        
        # Get price data
        prices = self.data[self.symbol]['close'].values[:self.current_index + 1]
        highs = self.data[self.symbol]['high'].values[:self.current_index + 1]
        lows = self.data[self.symbol]['low'].values[:self.current_index + 1]
        
        # Calculate indicators
        middle_band, upper_band, lower_band = TechnicalIndicators.bollinger_bands(
            prices, self.bb_period, self.bb_std
        )
        
        rsi = TechnicalIndicators.rsi(prices, self.rsi_period)
        
        atr = TechnicalIndicators.atr(highs, lows, prices, self.atr_period)
        
        # Current price and indicators
        current_price = current_data['close']
        current_middle = middle_band[-1]
        current_upper = upper_band[-1]
        current_lower = lower_band[-1]
        current_rsi = rsi[-1]
        current_atr = atr[-1]
        
        # Entry and exit logic
        if not self.in_position:
            # Oversold condition: price below lower band and RSI below oversold level
            if current_price <= current_lower and current_rsi <= self.rsi_oversold:
                # Calculate stop loss and take profit
                stop_loss = current_price - (current_atr * self.stop_loss_atr_multiple)
                take_profit = current_price + (current_atr * self.take_profit_atr_multiple)
                
                # Calculate position size based on risk
                position_size = self.calculate_position_size(current_price, stop_loss)
                
                logger.info(f"{self.current_time}: BUY {self.symbol} @ {current_price:.2f} (Stop: {stop_loss:.2f}, Target: {take_profit:.2f})")
                order = self.buy(self.symbol, position_size)
                
                # Set the stop loss and take profit for the position
                if len(self.get_open_positions(self.symbol)) > 0:
                    position = self.get_open_positions(self.symbol)[0]
                    position.stop_loss = stop_loss
                    position.take_profit = take_profit
                
                self.in_position = True
            
            # Overbought condition: price above upper band and RSI above overbought level
            elif current_price >= current_upper and current_rsi >= self.rsi_overbought:
                # Calculate stop loss and take profit
                stop_loss = current_price + (current_atr * self.stop_loss_atr_multiple)
                take_profit = current_price - (current_atr * self.take_profit_atr_multiple)
                
                # Calculate position size based on risk
                position_size = self.calculate_position_size(current_price, stop_loss)
                
                logger.info(f"{self.current_time}: SELL {self.symbol} @ {current_price:.2f} (Stop: {stop_loss:.2f}, Target: {take_profit:.2f})")
                order = self.sell(self.symbol, position_size)
                
                # Set the stop loss and take profit for the position
                if len(self.get_open_positions(self.symbol)) > 0:
                    position = self.get_open_positions(self.symbol)[0]
                    position.stop_loss = stop_loss
                    position.take_profit = take_profit
                
                self.in_position = True
        
        else:  # In position
            positions = self.get_open_positions(self.symbol)
            if not positions:
                self.in_position = False
                return
            
            # Additional exit condition: price crosses the middle band
            position = positions[0]
            
            if position.direction == 'long' and current_price >= current_middle:
                logger.info(f"{self.current_time}: EXIT LONG {self.symbol} @ {current_price:.2f} (Middle band)")
                self.close_position(position)
                self.in_position = False
            
            elif position.direction == 'short' and current_price <= current_middle:
                logger.info(f"{self.current_time}: EXIT SHORT {self.symbol} @ {current_price:.2f} (Middle band)")
                self.close_position(position)
                self.in_position = False


class BreakoutStrategy(AdvancedStrategy):
    """
    Breakout Strategy using price channels and volume confirmation.
    
    This strategy identifies consolidation periods and enters positions when
    price breaks out of the range with increased volume.
    """
    
    def __init__(self, symbol, channel_period=20, volume_factor=1.5, 
                 consolidation_factor=0.5, risk_per_trade=0.02, atr_period=14,
                 stop_loss_atr_multiple=1.5, take_profit_at<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>