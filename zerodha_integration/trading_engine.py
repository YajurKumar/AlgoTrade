"""
Trading engine module for Zerodha integration.
This module provides a unified interface to connect trading strategies with Zerodha's API.
"""

import logging
import time
import threading
import queue
import pandas as pd
import os
import json
from datetime import datetime, timedelta

from .auth import ZerodhaAuth
from .orders import OrderManager, OrderType, ProductType, TransactionType, Validity
from .market_data import MarketData

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zerodha_trading_engine')

class TradingEngine:
    """
    Trading engine that connects strategies with Zerodha's API.
    """
    
    def __init__(self, config_file=None, api_key=None, api_secret=None, redirect_url=None):
        """
        Initialize the trading engine.
        
        Parameters:
        -----------
        config_file : str, optional
            Path to a config file containing API credentials.
        api_key : str, optional
            Zerodha API key.
        api_secret : str, optional
            Zerodha API secret.
        redirect_url : str, optional
            Redirect URL registered with Zerodha.
        """
        self.auth = ZerodhaAuth(
            api_key=api_key,
            api_secret=api_secret,
            redirect_url=redirect_url,
            config_file=config_file
        )
        
        self.order_manager = OrderManager()
        self.market_data = MarketData()
        
        self.strategies = []
        self.running = False
        self.event_queue = queue.Queue()
        self.event_thread = None
        
        self.watchlist = set()
        self.positions = {}
        self.orders = {}
        
        # Initialize Kite Connect if credentials are available
        if self.auth.kite:
            self.order_manager.set_kite(self.auth.kite)
            self.market_data.set_kite(self.auth.kite)
    
    def login(self, open_browser=True):
        """
        Login to Zerodha.
        
        Parameters:
        -----------
        open_browser : bool, optional
            Whether to open the login URL in a browser.
            
        Returns:
        --------
        str
            The login URL.
        """
        return self.auth.login(open_browser=open_browser)
    
    def complete_login(self, redirect_url):
        """
        Complete the login flow.
        
        Parameters:
        -----------
        redirect_url : str
            The URL to which the user was redirected after login.
            
        Returns:
        --------
        bool
            True if login was completed successfully, False otherwise.
        """
        success = self.auth.complete_login(redirect_url)
        
        if success:
            # Update Kite Connect instance in order manager and market data
            self.order_manager.set_kite(self.auth.kite)
            self.market_data.set_kite(self.auth.kite)
        
        return success
    
    def is_authenticated(self):
        """
        Check if the user is authenticated.
        
        Returns:
        --------
        bool
            True if authenticated, False otherwise.
        """
        return self.auth.is_authenticated()
    
    def add_strategy(self, strategy):
        """
        Add a strategy to the trading engine.
        
        Parameters:
        -----------
        strategy : object
            The strategy object.
        """
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")
    
    def remove_strategy(self, strategy):
        """
        Remove a strategy from the trading engine.
        
        Parameters:
        -----------
        strategy : object
            The strategy object.
            
        Returns:
        --------
        bool
            True if the strategy was removed, False otherwise.
        """
        if strategy in self.strategies:
            self.strategies.remove(strategy)
            logger.info(f"Removed strategy: {strategy.name}")
            return True
        else:
            logger.warning(f"Strategy not found: {strategy.name}")
            return False
    
    def add_to_watchlist(self, symbols):
        """
        Add symbols to the watchlist.
        
        Parameters:
        -----------
        symbols : str or list
            Trading symbol(s) with exchange prefix (e.g., 'NSE:RELIANCE').
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        for symbol in symbols:
            self.watchlist.add(symbol)
        
        logger.info(f"Added {len(symbols)} symbols to watchlist")
    
    def remove_from_watchlist(self, symbols):
        """
        Remove symbols from the watchlist.
        
        Parameters:
        -----------
        symbols : str or list
            Trading symbol(s) with exchange prefix (e.g., 'NSE:RELIANCE').
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        for symbol in symbols:
            if symbol in self.watchlist:
                self.watchlist.remove(symbol)
        
        logger.info(f"Removed {len(symbols)} symbols from watchlist")
    
    def start(self, mode='paper'):
        """
        Start the trading engine.
        
        Parameters:
        -----------
        mode : str, optional
            Trading mode ('live' or 'paper').
        """
        if self.running:
            logger.warning("Trading engine is already running")
            return
        
        if mode == 'live' and not self.is_authenticated():
            logger.error("Cannot start live trading without authentication")
            return
        
        self.running = True
        self.mode = mode
        
        # Start event processing thread
        self.event_thread = threading.Thread(target=self._process_events)
        self.event_thread.daemon = True
        self.event_thread.start()
        
        logger.info(f"Started trading engine in {mode} mode")
        
        # Initialize strategies
        for strategy in self.strategies:
            strategy.initialize()
        
        # Update positions and orders
        self._update_positions_and_orders()
    
    def stop(self):
        """
        Stop the trading engine.
        """
        if not self.running:
            logger.warning("Trading engine is not running")
            return
        
        self.running = False
        
        # Wait for event thread to finish
        if self.event_thread and self.event_thread.is_alive():
            self.event_thread.join(timeout=5)
        
        logger.info("Stopped trading engine")
    
    def _process_events(self):
        """
        Process events from the event queue.
        """
        while self.running:
            try:
                # Get event from queue with timeout
                try:
                    event = self.event_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process event
                event_type = event.get('type')
                
                if event_type == 'tick':
                    self._process_tick_event(event)
                elif event_type == 'order_update':
                    self._process_order_update_event(event)
                elif event_type == 'position_update':
                    self._process_position_update_event(event)
                
                # Mark event as processed
                self.event_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
    
    def _process_tick_event(self, event):
        """
        Process a tick event.
        
        Parameters:
        -----------
        event : dict
            The tick event.
        """
        tick_data = event.get('data', {})
        
        # Update strategies with tick data
        for strategy in self.strategies:
            if hasattr(strategy, 'on_tick'):
                strategy.on_tick(tick_data)
    
    def _process_order_update_event(self, event):
        """
        Process an order update event.
        
        Parameters:
        -----------
        event : dict
            The order update event.
        """
        order_data = event.get('data', {})
        order_id = order_data.get('order_id')
        
        # Update orders dictionary
        if order_id:
            self.orders[order_id] = order_data
        
        # Update strategies with order update
        for strategy in self.strategies:
            if hasattr(strategy, 'on_order_update'):
                strategy.on_order_update(order_data)
    
    def _process_position_update_event(self, event):
        """
        Process a position update event.
        
        Parameters:
        -----------
        event : dict
            The position update event.
        """
        position_data = event.get('data', {})
        symbol = position_data.get('symbol')
        
        # Update positions dictionary
        if symbol:
            self.positions[symbol] = position_data
        
        # Update strategies with position update
        for strategy in self.strategies:
            if hasattr(strategy, 'on_position_update'):
                strategy.on_position_update(position_data)
    
    def _update_positions_and_orders(self):
        """
        Update positions and orders from Zerodha.
        """
        if not self.is_authenticated() or self.mode != 'live':
            return
        
        try:
            # Update positions
            positions_data = self.market_data.get_positions()
            if positions_data:
                for position in positions_data.get('net', []):
                    symbol = f"{position['exchange']}:{position['tradingsymbol']}"
                    self.positions[symbol] = position
            
            # Update orders
            orders_data = self.order_manager.get_order_history()
            for order in orders_data:
                self.orders[order['order_id']] = order
            
            logger.info(f"Updated {len(self.positions)} positions and {len(self.orders)} orders")
        
        except Exception as e:
            logger.error(f"Error updating positions and orders: {str(e)}")
    
    def place_order(self, symbol, exchange, transaction_type, quantity, 
                   order_type=OrderType.MARKET, product_type=ProductType.NORMAL,
                   price=None, trigger_price=None, tag=None):
        """
        Place an order.
        
        Parameters:
        -----------
        symbol : str
            Trading symbol.
        exchange : str
            Exchange (NSE, BSE, NFO, etc.).
        transaction_type : TransactionType
            BUY or SELL.
        quantity : int
            Order quantity.
        order_type : OrderType, optional
            Order type (MARKET, LIMIT, SL, SL-M).
        product_type : ProductType, optional
            Product type (INTRADAY, DELIVERY, NORMAL, COVER, BRACKET).
        price : float, optional
            Order price, required for LIMIT and SL orders.
        trigger_price : float, optional
            Trigger price, required for SL and SL-M orders.
        tag : str, optional
            Tag for the order.
            
        Returns:
        --------
        str
            Order ID if successful, None otherwise.
        """
        if self.mode == 'paper':
            # Simulate order placement in paper trading mode
            order_id = f"PAPER-{int(time.time())}"
            logger.info(f"Paper trading: Placed order {order_id} - {transaction_type.value} {quantity} {symbol} @ {order_type.value}")
            
            # Create a simulated order update
            order_data = {
                'order_id': order_id,
                'status': 'COMPLETE',
                'tradingsymbol': symbol,
                'exchange': exchange,
                'transaction_type': transaction_type.value,
                'quantity': quantity,
                'product': product_type.value,
                'order_type': order_type.value,
                'price': price,
                'trigger_price': trigger_price,
                'tag': tag,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add to orders dictionary
            self.orders[order_id] = order_data
            
            # Create a simulated position update
            if transaction_type == TransactionType.BUY:
                position_quantity = quantity
            else:
                position_quantity = -quantity
            
            position_data = {
                'symbol': f"{exchange}:{symbol}",
                'quantity': position_quantity,
                'product': product_type.value,
                'price': price or self._get_simulated_price(f"{exchange}:{symbol}")
            }
            
            # Add to positions dictionary
            self.positions[f"{exchange}:{symbol}"] = position_data
            
            # Add order update event to queue
            self.event_queue.put({
                'type': 'order_update',
                'data': order_data
            })
            
            # Add position update event to queue
            self.event_queue.put({
                'type': 'position_update',
                'data': position_data
            })
            
            return order_id
        
        else:
            # Place real order in live trading mode
            return self.order_manager.place_order(
                symbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product_type=product_type,
                price=price,
                trigger_price=trigger_price,
                tag=tag
            )
    
    def _get_simulated_price(self, symbol):
        """
        Get a simulated price for paper trading.
        
        Parameters:
        -----------
        symbol : str
            Trading symbol with exchange prefix.
            
        Returns:
        --------
        float
            Simulated price.
        """
        # Try to get the last price from market data
        try:
            ltp_data = self.market_data.get_ltp([symbol])
            if ltp_data and symbol in ltp_data:
                return ltp_data[symbol]['last_price']
        except:
            pass
        
        # Return a default price if unable to get real price
        return 100.0
    
    def modify_order(self, order_id, quantity=None, price=None, 
                    order_type=None, trigger_price=None):
        """
        Modify an order.
        
        Parameters:
        -----------
        order_id : str
            Order ID to modify.
        quantity : int, optional
            New order quantity.
        price : float, optional
            New order price.
        order_type : OrderType, optional
            New order type.
        trigger_price : float, optional
            New trigger price.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        if self.mode == 'paper':
            # Simulate order modification in paper trading mode
            if order_id in self.orders:
                order_data = self.orders[order_id]
                
                # Update order data
                if quantity is not None:
                    order_data['quantity'] = quantity
                
                if price is not None:
                    order_data['price'] = price
                
                if order_type is not None:
                    order_data['order_type'] = order_type.value if isinstance<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>