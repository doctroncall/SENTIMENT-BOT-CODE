"""
SMC Trading Bot
Executes trades based on Smart Money Concepts analysis
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import MetaTrader5 as mt5

from mt5_connector import MT5Connector
from smc_analyzer import SMCAnalyzer


class SMCTradingBot:
    """Production trading bot using SMC strategy"""
    
    def __init__(self, config: Dict):
        """
        Initialize trading bot
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.mt5 = MT5Connector(config['mt5'])
        self.smc = SMCAnalyzer(config['smc'])
        
        # Trading parameters
        self.symbols = config['trading']['symbols']
        self.timeframe = self._get_timeframe(config['trading']['timeframe'])
        self.lot_size = config['trading']['lot_size']
        self.max_positions = config['trading']['max_positions']
        self.risk_reward = config['trading']['risk_reward']
        self.risk_percent = config['trading']['risk_percent']
        
        # State
        self.running = False
        self.positions_count = 0
        
    def _get_timeframe(self, tf_str: str) -> int:
        """Convert timeframe string to MT5 constant"""
        timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
        }
        return timeframes.get(tf_str, mt5.TIMEFRAME_H1)
    
    def calculate_position_size(self, symbol: str, sl_points: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Trading symbol
            sl_points: Stop loss distance in points
            
        Returns:
            Position size in lots
        """
        account_info = self.mt5.get_account_info()
        if not account_info:
            return self.lot_size
        
        balance = account_info['balance']
        risk_amount = balance * (self.risk_percent / 100)
        
        # Get symbol info for point value
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return self.lot_size
        
        point_value = symbol_info.trade_tick_value
        lot_size = risk_amount / (sl_points * point_value)
        
        # Round to symbol's volume step
        volume_step = symbol_info.volume_step
        lot_size = round(lot_size / volume_step) * volume_step
        
        # Ensure within min/max limits
        lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
        
        return lot_size
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Analyze a symbol and generate trading decision
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Trading decision dictionary or None
        """
        self.logger.info(f"Analyzing {symbol}...")
        
        # Get historical data
        df = self.mt5.get_historical_data(symbol, self.timeframe, bars=500)
        if df is None or len(df) < 100:
            self.logger.warning(f"Insufficient data for {symbol}")
            return None
        
        # Perform SMC analysis
        analysis = self.smc.analyze(df)
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        current_price = (tick.bid + tick.ask) / 2
        
        # Get trading signal
        signal = self.smc.get_trading_signal(analysis, current_price)
        
        if signal is None:
            return None
        
        # Calculate SL and TP
        market_structure = analysis['market_structure']
        
        if signal == 'BUY':
            # Set SL below recent swing low
            swing_lows = analysis['swing_points']['lows']
            if len(swing_lows) > 0:
                sl = swing_lows[-1]['low']
            else:
                sl = current_price * 0.99  # 1% SL as fallback
            
            sl_distance = current_price - sl
            tp = current_price + (sl_distance * self.risk_reward)
            
        else:  # SELL
            # Set SL above recent swing high
            swing_highs = analysis['swing_points']['highs']
            if len(swing_highs) > 0:
                sl = swing_highs[-1]['high']
            else:
                sl = current_price * 1.01  # 1% SL as fallback
            
            sl_distance = sl - current_price
            tp = current_price - (sl_distance * self.risk_reward)
        
        # Calculate position size
        symbol_info = mt5.symbol_info(symbol)
        sl_points = abs(current_price - sl) / symbol_info.point
        lot_size = self.calculate_position_size(symbol, sl_points)
        
        return {
            'symbol': symbol,
            'signal': signal,
            'price': current_price,
            'sl': sl,
            'tp': tp,
            'lot_size': lot_size,
            'analysis': analysis
        }
    
    def execute_trade(self, decision: Dict) -> bool:
        """
        Execute a trade based on decision
        
        Args:
            decision: Trading decision dictionary
            
        Returns:
            bool: True if trade executed successfully
        """
        # Check position limit
        current_positions = len(self.mt5.get_positions())
        if current_positions >= self.max_positions:
            self.logger.warning(f"Max positions ({self.max_positions}) reached")
            return False
        
        # Place order
        result = self.mt5.place_order(
            symbol=decision['symbol'],
            order_type=decision['signal'],
            volume=decision['lot_size'],
            sl=decision['sl'],
            tp=decision['tp'],
            comment=f"SMC {decision['signal']}"
        )
        
        if result:
            self.logger.info(f"Trade executed: {decision['signal']} {decision['lot_size']} {decision['symbol']}")
            self.positions_count += 1
            return True
        
        return False
    
    def manage_positions(self):
        """Manage existing positions (trailing stop, etc.)"""
        positions = self.mt5.get_positions()
        
        for pos in positions:
            # Simple trailing stop logic
            if pos['profit'] > 0:
                # Move SL to breakeven if profit is positive
                if pos['type'] == 'BUY':
                    if pos['sl'] < pos['price_open']:
                        # Could implement trailing stop here
                        pass
                else:  # SELL
                    if pos['sl'] > pos['price_open']:
                        # Could implement trailing stop here
                        pass
    
    def run(self):
        """Main bot loop"""
        self.logger.info("Starting SMC Trading Bot...")
        
        # Connect to MT5
        if not self.mt5.connect():
            self.logger.error("Failed to connect to MT5. Exiting.")
            return
        
        self.running = True
        scan_interval = self.config['trading'].get('scan_interval', 60)  # seconds
        
        try:
            while self.running:
                self.logger.info("=== New scan cycle ===")
                
                # Get account info
                account = self.mt5.get_account_info()
                if account:
                    self.logger.info(f"Account - Balance: {account['balance']}, Equity: {account['equity']}, Profit: {account['profit']}")
                
                # Manage existing positions
                self.manage_positions()
                
                # Scan all symbols
                for symbol in self.symbols:
                    try:
                        decision = self.analyze_symbol(symbol)
                        
                        if decision:
                            self.logger.info(f"Trading opportunity found for {symbol}: {decision['signal']}")
                            self.execute_trade(decision)
                    
                    except Exception as e:
                        self.logger.error(f"Error analyzing {symbol}: {str(e)}")
                        continue
                
                # Wait before next scan
                self.logger.info(f"Waiting {scan_interval} seconds until next scan...")
                time.sleep(scan_interval)
        
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        
        except Exception as e:
            self.logger.error(f"Bot error: {str(e)}")
        
        finally:
            self.mt5.disconnect()
            self.logger.info("Bot shutdown complete")
    
    def stop(self):
        """Stop the bot"""
        self.running = False
