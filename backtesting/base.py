"""
Base classes for the backtesting framework.
This module provides the core components for backtesting trading strategies.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import os
import sys

# Add the parent directory to the path so we can import the data_fetcher module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from data_fetcher.normalizer import prepare_data_for_backtesting

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('backtesting')

class Position:
    """
    Represents a trading position (long or short).
    """
    
    def __init__(self, symbol, entry_price, entry_time, quantity, direction, stop_loss=None, take_profit=None):
        """
        Initialize a new position.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        entry_price : float
            The price at which the position was entered.
        entry_time : datetime
            The time at which the position was entered.
        quantity : float
            The quantity of the asset.
        direction : str
            The direction of the position ('long' or 'short').
        stop_loss : float, optional
            The stop loss price.
        take_profit : float, optional
            The take profit price.
        """
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.quantity = quantity
        self.direction = direction.lower()
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0
        self.status = 'open'
    
    def close(self, exit_price, exit_time):
        """
        Close the position.
        
        Parameters:
        -----------
        exit_price : float
            The price at which the position was closed.
        exit_time : datetime
            The time at which the position was closed.
            
        Returns:
        --------
        float
            The profit or loss from the position.
        """
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.status = 'closed'
        
        if self.direction == 'long':
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:  # short
            self.pnl = (self.entry_price - exit_price) * self.quantity
        
        return self.pnl
    
    def calculate_current_pnl(self, current_price):
        """
        Calculate the current unrealized profit or loss.
        
        Parameters:
        -----------
        current_price : float
            The current price of the asset.
            
        Returns:
        --------
        float
            The current unrealized profit or loss.
        """
        if self.status == 'closed':
            return self.pnl
        
        if self.direction == 'long':
            return (current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - current_price) * self.quantity
    
    def check_stop_loss(self, current_price):
        """
        Check if the stop loss has been triggered.
        
        Parameters:
        -----------
        current_price : float
            The current price of the asset.
            
        Returns:
        --------
        bool
            True if the stop loss has been triggered, False otherwise.
        """
        if self.stop_loss is None:
            return False
        
        if self.direction == 'long':
            return current_price <= self.stop_loss
        else:  # short
            return current_price >= self.stop_loss
    
    def check_take_profit(self, current_price):
        """
        Check if the take profit has been triggered.
        
        Parameters:
        -----------
        current_price : float
            The current price of the asset.
            
        Returns:
        --------
        bool
            True if the take profit has been triggered, False otherwise.
        """
        if self.take_profit is None:
            return False
        
        if self.direction == 'long':
            return current_price >= self.take_profit
        else:  # short
            return current_price <= self.take_profit
    
    def __str__(self):
        """
        String representation of the position.
        
        Returns:
        --------
        str
            String representation.
        """
        status_str = f"{self.direction.upper()} {self.quantity} {self.symbol} @ {self.entry_price}"
        if self.status == 'closed':
            pnl_str = f"PnL: {self.pnl:.2f}"
            return f"{status_str} [CLOSED @ {self.exit_price}] {pnl_str}"
        else:
            sl_str = f"SL: {self.stop_loss}" if self.stop_loss else ""
            tp_str = f"TP: {self.take_profit}" if self.take_profit else ""
            return f"{status_str} [OPEN] {sl_str} {tp_str}"


class Order:
    """
    Represents a trading order.
    """
    
    def __init__(self, symbol, order_type, quantity, direction, price=None, stop_price=None, limit_price=None):
        """
        Initialize a new order.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        order_type : str
            The type of order ('market', 'limit', 'stop', 'stop_limit').
        quantity : float
            The quantity of the asset.
        direction : str
            The direction of the order ('buy' or 'sell').
        price : float, optional
            The price for limit orders.
        stop_price : float, optional
            The stop price for stop orders.
        limit_price : float, optional
            The limit price for stop-limit orders.
        """
        self.symbol = symbol
        self.order_type = order_type.lower()
        self.quantity = quantity
        self.direction = direction.lower()
        self.price = price
        self.stop_price = stop_price
        self.limit_price = limit_price
        self.status = 'pending'
        self.filled_price = None
        self.filled_time = None
    
    def fill(self, price, time):
        """
        Fill the order.
        
        Parameters:
        -----------
        price : float
            The price at which the order was filled.
        time : datetime
            The time at which the order was filled.
            
        Returns:
        --------
        bool
            True if the order was filled successfully, False otherwise.
        """
        self.filled_price = price
        self.filled_time = time
        self.status = 'filled'
        return True
    
    def cancel(self):
        """
        Cancel the order.
        
        Returns:
        --------
        bool
            True if the order was cancelled successfully, False otherwise.
        """
        if self.status == 'filled':
            return False
        
        self.status = 'cancelled'
        return True
    
    def is_executable(self, current_price):
        """
        Check if the order can be executed at the current price.
        
        Parameters:
        -----------
        current_price : float
            The current price of the asset.
            
        Returns:
        --------
        bool
            True if the order can be executed, False otherwise.
        """
        if self.status != 'pending':
            return False
        
        if self.order_type == 'market':
            return True
        
        elif self.order_type == 'limit':
            if self.direction == 'buy':
                return current_price <= self.price
            else:  # sell
                return current_price >= self.price
        
        elif self.order_type == 'stop':
            if self.direction == 'buy':
                return current_price >= self.stop_price
            else:  # sell
                return current_price <= self.stop_price
        
        elif self.order_type == 'stop_limit':
            if self.direction == 'buy':
                return (current_price >= self.stop_price) and (current_price <= self.limit_price)
            else:  # sell
                return (current_price <= self.stop_price) and (current_price >= self.limit_price)
        
        return False
    
    def __str__(self):
        """
        String representation of the order.
        
        Returns:
        --------
        str
            String representation.
        """
        direction_str = self.direction.upper()
        type_str = self.order_type.upper()
        
        if self.order_type == 'market':
            return f"{direction_str} {self.quantity} {self.symbol} @ MARKET [{self.status.upper()}]"
        
        elif self.order_type == 'limit':
            return f"{direction_str} {self.quantity} {self.symbol} @ LIMIT {self.price} [{self.status.upper()}]"
        
        elif self.order_type == 'stop':
            return f"{direction_str} {self.quantity} {self.symbol} @ STOP {self.stop_price} [{self.status.upper()}]"
        
        elif self.order_type == 'stop_limit':
            return f"{direction_str} {self.quantity} {self.symbol} @ STOP-LIMIT {self.stop_price}/{self.limit_price} [{self.status.upper()}]"
        
        return f"{direction_str} {self.quantity} {self.symbol} [{self.status.upper()}]"


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """
    
    def __init__(self, name=None):
        """
        Initialize a new strategy.
        
        Parameters:
        -----------
        name : str, optional
            The name of the strategy.
        """
        self.name = name or self.__class__.__name__
        self.positions = []
        self.orders = []
        self.trades = []
        self.data = None
        self.current_time = None
        self.current_index = 0
        self.initial_capital = 0
        self.cash = 0
        self.equity = 0
        self.equity_curve = []
    
    @abstractmethod
    def initialize(self):
        """
        Initialize the strategy. This method is called once at the beginning of the backtest.
        """
        pass
    
    @abstractmethod
    def next(self, data):
        """
        Process the next data point. This method is called for each data point in the backtest.
        
        Parameters:
        -----------
        data : pandas.DataFrame
            The current data point.
        """
        pass
    
    def buy(self, symbol, quantity, price=None, stop_loss=None, take_profit=None):
        """
        Create a buy order.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        quantity : float
            The quantity to buy.
        price : float, optional
            The price to buy at. If None, a market order is created.
        stop_loss : float, optional
            The stop loss price.
        take_profit : float, optional
            The take profit price.
            
        Returns:
        --------
        Order
            The created order.
        """
        if price is None:
            order = Order(symbol, 'market', quantity, 'buy')
        else:
            order = Order(symbol, 'limit', quantity, 'buy', price=price)
        
        self.orders.append(order)
        return order
    
    def sell(self, symbol, quantity, price=None, stop_loss=None, take_profit=None):
        """
        Create a sell order.
        
        Parameters:
        -----------
        symbol : str
            The trading symbol.
        quantity : float
            The quantity to sell.
        price : float, optional
            The price to sell at. If None, a market order is created.
        stop_loss : float, optional
            The stop loss price.
        take_profit : float, optional
            The take profit price.
            
        Returns:
        --------
        Order
            The created order.
        """
        if price is None:
            order = Order(symbol, 'market', quantity, 'sell')
        else:
            order = Order(symbol, 'limit', quantity, 'sell', price=price)
        
        self.orders.append(order)
        return order
    
    def close_position(self, position, price=None):
        """
        Close a position.
        
        Parameters:
        -----------
        position : Position
            The position to close.
        price : float, optional
            The price to close at. If None, a market order is created.
            
        Returns:
        --------
        Order
            The created order.
        """
        if position.status == 'closed':
            return None
        
        if position.direction == 'long':
            return self.sell(position.symbol, position.quantity, price)
        else:  # short
            return self.buy(position.symbol, position.quantity, price)
    
    def get_open_positions(self, symbol=None):
        """
        Get all open positions.
        
        Parameters:
        -----------
        symbol : str, optional
            Filter positions by symbol.
            
        Returns:
        --------
        list
            List of open positions.
        """
        if symbol:
            return [p for p in self.positions if p.status == 'open' and p.symbol == symbol]
        else:
            return [p for p in self.positions if p.status == 'open']
    
    def get_pending_orders(self, symbol=None):
        """
        Get all pending orders.
        
        Parameters:
        -----------
        symbol : str, optional
            Filter orders by symbol.
            
        Returns:
        --------
        list
            List of pending orders.
        """
        if symbol:
            return [o for o in self.orders if o.status == 'pending' and o.symbol == symbol]
        else:
            return [o for o in self.orders if o.status == 'pending']
    
    def calculate_equity(self, current_prices):
        """
        Calculate the current equity.
        
        Parameters:
        -----------
        current_prices : dict
            Dictionary mapping symbols to current prices.
            
        Returns:
        --------
        float
            The current equity.
        """
        equity = self.cash
        
        for position in self.get_open_positions():
            if position.symbol in current_prices:
                equity += position.calculate_current_pnl(current_prices[position.symbol])
        
        return equity


class Backtester:
    """
    Class for backtesting trading strategies.
    """
    
    def __init__(self, strategy, data, initial_capital=100000.0, commission=0.0):
        """
        Initialize a new backtester.
        
        Parameters:
        -----------
        strategy : Strategy
            The trading strategy to backtest.
        data : pandas.DataFrame or dict
            The historical data to use for backtesting.
            If a DataFrame, it should have a DatetimeIndex and contain OHLCV data.
            If a dict, keys should be symbols and values should be DataFrames with OHLCV data.
        initial_capital : float, optional
            The initial capital to start with.
        commission : float, optional
            The commission rate per trade (as a percentage).
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        
        # Convert data to a dictionary if it's a DataFrame
        if isinstance(data, pd.DataFrame):
            self.data = {'default': data}
        else:
            self.data = dat<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>