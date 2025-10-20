"""
MT5 Connector Module for Windows
Handles all MetaTrader 5 connections and operations
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
import time


class MT5Connector:
    """Production-grade MT5 connector for Windows"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MT5 connector
        
        Args:
            config: Configuration dictionary containing MT5 settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.account_info = None
        
    def connect(self, max_retries: int = 3) -> bool:
        """
        Connect to MT5 terminal with retry logic
        
        Args:
            max_retries: Maximum number of connection attempts
            
        Returns:
            bool: True if connected successfully
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempting to connect to MT5 (attempt {attempt + 1}/{max_retries})")
                
                # Initialize MT5 connection
                if not mt5.initialize():
                    error = mt5.last_error()
                    self.logger.error(f"MT5 initialization failed: {error}")
                    time.sleep(2)
                    continue
                
                # Login if credentials provided
                if self.config.get('account') and self.config.get('password'):
                    login = self.config['account']
                    password = self.config['password']
                    server = self.config.get('server', '')
                    
                    if not mt5.login(login, password, server):
                        error = mt5.last_error()
                        self.logger.error(f"MT5 login failed: {error}")
                        mt5.shutdown()
                        time.sleep(2)
                        continue
                
                # Verify connection
                self.account_info = mt5.account_info()
                if self.account_info is None:
                    self.logger.error("Failed to get account info")
                    mt5.shutdown()
                    time.sleep(2)
                    continue
                
                self.connected = True
                self.logger.info(f"Successfully connected to MT5. Account: {self.account_info.login}")
                self.logger.info(f"Balance: {self.account_info.balance}, Equity: {self.account_info.equity}")
                return True
                
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
        
        self.logger.error("Failed to connect to MT5 after all retries")
        return False
    
    def disconnect(self):
        """Safely disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Disconnected from MT5")
    
    def get_historical_data(
        self, 
        symbol: str, 
        timeframe: int, 
        bars: int = 1000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_H1)
            bars: Number of bars to retrieve
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        try:
            # Ensure symbol is available
            if not mt5.symbol_select(symbol, True):
                self.logger.error(f"Failed to select symbol {symbol}")
                return None
            
            # Get rates
            if start_date and end_date:
                rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            
            if rates is None or len(rates) == 0:
                self.logger.error(f"Failed to get rates for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            self.logger.info(f"Retrieved {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {str(e)}")
            return None
    
    def get_symbols(self) -> List[str]:
        """
        Get list of available symbols
        
        Returns:
            List of symbol names
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return []
        
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            
            return [s.name for s in symbols if s.visible]
            
        except Exception as e:
            self.logger.error(f"Error getting symbols: {str(e)}")
            return []
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get current account information
        
        Returns:
            Dictionary with account details or None
        """
        if not self.connected:
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'login': info.login,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'margin_level': info.margin_level,
                'profit': info.profit,
                'currency': info.currency,
                'leverage': info.leverage,
                'server': info.server
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {str(e)}")
            return None
    
    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = ""
    ) -> Optional[Dict]:
        """
        Place a trading order
        
        Args:
            symbol: Trading symbol
            order_type: 'BUY' or 'SELL'
            volume: Order volume in lots
            price: Order price (None for market orders)
            sl: Stop loss price
            tp: Take profit price
            deviation: Maximum price deviation in points
            comment: Order comment
            
        Returns:
            Order result dictionary or None
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        try:
            # Prepare order request
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Symbol {symbol} not found")
                return None
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    self.logger.error(f"Failed to select {symbol}")
                    return None
            
            # Determine order type
            if order_type.upper() == 'BUY':
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = price or mt5.symbol_info_tick(symbol).ask
            elif order_type.upper() == 'SELL':
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = price or mt5.symbol_info_tick(symbol).bid
            else:
                self.logger.error(f"Invalid order type: {order_type}")
                return None
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "deviation": deviation,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error("Order send failed: No result")
                return None
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            self.logger.info(f"Order placed successfully: {order_type} {volume} {symbol} @ {price}")
            
            return {
                'order': result.order,
                'volume': result.volume,
                'price': result.price,
                'retcode': result.retcode,
                'comment': result.comment
            }
            
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions
        
        Returns:
            List of position dictionaries
        """
        if not self.connected:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def close_position(self, ticket: int) -> bool:
        """
        Close a position by ticket number
        
        Args:
            ticket: Position ticket number
            
        Returns:
            bool: True if closed successfully
        """
        if not self.connected:
            return False
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                self.logger.error(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            # Prepare close request
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(position.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Failed to close position {ticket}")
                return False
            
            self.logger.info(f"Position {ticket} closed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing position: {str(e)}")
            return False
