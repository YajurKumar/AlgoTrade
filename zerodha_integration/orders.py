"""
Order management module for Zerodha Kite Connect API.
This module provides functionality to place, modify, and cancel orders with Zerodha.
"""

import logging
import time
from kiteconnect import KiteConnect
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zerodha_orders')

class OrderType(Enum):
    """Enum for order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_MARKET = "SL-M"

class ProductType(Enum):
    """Enum for product types."""
    INTRADAY = "MIS"
    DELIVERY = "CNC"
    NORMAL = "NRML"
    COVER = "CO"
    BRACKET = "BO"

class TransactionType(Enum):
    """Enum for transaction types."""
    BUY = "BUY"
    SELL = "SELL"

class Validity(Enum):
    """Enum for order validity."""
    DAY = "DAY"
    IOC = "IOC"

class OrderManager:
    """
    Class to manage orders with Zerodha's Kite Connect API.
    """
    
    def __init__(self, kite=None):
        """
        Initialize the order manager.
        
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
    
    def place_order(self, symbol, exchange, transaction_type, quantity, 
                   order_type=OrderType.MARKET, product_type=ProductType.NORMAL,
                   price=None, trigger_price=None, validity=Validity.DAY,
                   disclosed_quantity=None, tag=None):
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
        validity : Validity, optional
            Order validity (DAY, IOC).
        disclosed_quantity : int, optional
            Disclosed quantity.
        tag : str, optional
            Tag for the order.
            
        Returns:
        --------
        str
            Order ID if successful, None otherwise.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return None
        
        try:
            # Convert enum values to strings
            if isinstance(transaction_type, TransactionType):
                transaction_type = transaction_type.value
            
            if isinstance(order_type, OrderType):
                order_type = order_type.value
            
            if isinstance(product_type, ProductType):
                product_type = product_type.value
            
            if isinstance(validity, Validity):
                validity = validity.value
            
            # Prepare order parameters
            params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product_type,
                "validity": validity
            }
            
            # Add optional parameters if provided
            if price is not None:
                params["price"] = price
            
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            
            if disclosed_quantity is not None:
                params["disclosed_quantity"] = disclosed_quantity
            
            if tag is not None:
                params["tag"] = tag
            
            # Place the order
            order_id = self.kite.place_order(variety="regular", **params)
            logger.info(f"Placed order: {order_id} - {transaction_type} {quantity} {symbol} @ {order_type}")
            return order_id
        
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    def modify_order(self, order_id, quantity=None, price=None, 
                    order_type=None, trigger_price=None, validity=None,
                    disclosed_quantity=None):
        """
        Modify an existing order.
        
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
        validity : Validity, optional
            New order validity.
        disclosed_quantity : int, optional
            New disclosed quantity.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return False
        
        try:
            # Convert enum values to strings
            if isinstance(order_type, OrderType):
                order_type = order_type.value
            
            if isinstance(validity, Validity):
                validity = validity.value
            
            # Prepare parameters
            params = {"order_id": order_id}
            
            # Add optional parameters if provided
            if quantity is not None:
                params["quantity"] = quantity
            
            if price is not None:
                params["price"] = price
            
            if order_type is not None:
                params["order_type"] = order_type
            
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            
            if validity is not None:
                params["validity"] = validity
            
            if disclosed_quantity is not None:
                params["disclosed_quantity"] = disclosed_quantity
            
            # Modify the order
            self.kite.modify_order(variety="regular", **params)
            logger.info(f"Modified order: {order_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return False
    
    def cancel_order(self, order_id):
        """
        Cancel an order.
        
        Parameters:
        -----------
        order_id : str
            Order ID to cancel.
            
        Returns:
        --------
        bool
            True if successful, False otherwise.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return False
        
        try:
            self.kite.cancel_order(variety="regular", order_id=order_id)
            logger.info(f"Cancelled order: {order_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def get_order_history(self, order_id=None):
        """
        Get order history.
        
        Parameters:
        -----------
        order_id : str, optional
            Order ID to get history for. If None, gets all orders.
            
        Returns:
        --------
        list
            List of orders.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return []
        
        try:
            if order_id:
                orders = self.kite.order_history(order_id)
                logger.info(f"Got history for order: {order_id}")
            else:
                orders = self.kite.orders()
                logger.info("Got all orders")
            
            return orders
        
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            return []
    
    def get_trades(self, order_id=None):
        """
        Get trades.
        
        Parameters:
        -----------
        order_id : str, optional
            Order ID to get trades for. If None, gets all trades.
            
        Returns:
        --------
        list
            List of trades.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return []
        
        try:
            if order_id:
                trades = self.kite.order_trades(order_id)
                logger.info(f"Got trades for order: {order_id}")
            else:
                trades = self.kite.trades()
                logger.info("Got all trades")
            
            return trades
        
        except Exception as e:
            logger.error(f"Error getting trades: {str(e)}")
            return []
    
    def place_bracket_order(self, symbol, exchange, transaction_type, quantity,
                           price=None, trigger_price=None, target=None, stoploss=None,
                           trailing_stoploss=None, tag=None):
        """
        Place a bracket order.
        
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
        price : float, optional
            Order price, required for LIMIT orders.
        trigger_price : float, optional
            Trigger price, required for SL orders.
        target : float, optional
            Target price.
        stoploss : float, optional
            Stoploss price.
        trailing_stoploss : float, optional
            Trailing stoploss points.
        tag : str, optional
            Tag for the order.
            
        Returns:
        --------
        str
            Order ID if successful, None otherwise.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return None
        
        try:
            # Convert enum values to strings
            if isinstance(transaction_type, TransactionType):
                transaction_type = transaction_type.value
            
            # Prepare order parameters
            params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": "LIMIT",
                "product": "BO",
                "validity": "DAY"
            }
            
            # Add required parameters
            if price is not None:
                params["price"] = price
            else:
                logger.error("Price is required for bracket orders")
                return None
            
            if stoploss is not None:
                params["stoploss"] = stoploss
            else:
                logger.error("Stoploss is required for bracket orders")
                return None
            
            # Add optional parameters if provided
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            
            if target is not None:
                params["squareoff"] = target
            
            if trailing_stoploss is not None:
                params["trailing_stoploss"] = trailing_stoploss
            
            if tag is not None:
                params["tag"] = tag
            
            # Place the bracket order
            order_id = self.kite.place_order(variety="bo", **params)
            logger.info(f"Placed bracket order: {order_id} - {transaction_type} {quantity} {symbol} @ {price}")
            return order_id
        
        except Exception as e:
            logger.error(f"Error placing bracket order: {str(e)}")
            return None
    
    def place_cover_order(self, symbol, exchange, transaction_type, quantity,
                         price=None, trigger_price=None, tag=None):
        """
        Place a cover order.
        
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
        price : float, optional
            Order price for LIMIT orders. If None, uses MARKET order.
        trigger_price : float
            Trigger price for stoploss.
        tag : str, optional
            Tag for the order.
            
        Returns:
        --------
        str
            Order ID if successful, None otherwise.
        """
        if not self.kite:
            logger.error("KiteConnect not set. Use set_kite() first.")
            return None
        
        try:
            # Convert enum values to strings
            if isinstance(transaction_type, TransactionType):
                transaction_type = transaction_type.value
            
            # Determine order type
            order_type = "LIMIT" if price is not None else "MARKET"
            
            # Prepare order parameters
            params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": "CO",
                "validity": "DAY"
            }
            
            # Add optional parameters if provided
            if price is not None:
                params["price"] = price
            
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            else:
                logger.error("Trigger price is required for cover orders")
                return None
            
            if tag is not None:
                params["tag"] = tag
            
            # Place the cover order
            order_id = self.kite.place_order(variety="co", **params)
            logger.info(f"Placed cover order: {order_id} - {transaction_type} {quantity} {symbol} @ {order_type}")
            return order_id
        
        except Exception as e:
            logger.error(f"Error placing cover order: {str(e)}")
            return None
