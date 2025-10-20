"""
Smart Money Concepts (SMC) Analyzer
Identifies market structure, order blocks, and fair value gaps
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging


class SMCAnalyzer:
    """Analyzes price data using Smart Money Concepts"""
    
    def __init__(self, config: Dict):
        """
        Initialize SMC Analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.swing_lookback = config.get('swing_lookback', 10)
        self.fvg_min_gap = config.get('fvg_min_gap', 0.0001)
        
    def identify_swing_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify swing highs and swing lows
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with swing_high and swing_low columns
        """
        df = df.copy()
        lookback = self.swing_lookback
        
        df['swing_high'] = False
        df['swing_low'] = False
        
        for i in range(lookback, len(df) - lookback):
            # Check for swing high
            if df.iloc[i]['high'] == df.iloc[i - lookback:i + lookback + 1]['high'].max():
                df.at[df.index[i], 'swing_high'] = True
            
            # Check for swing low
            if df.iloc[i]['low'] == df.iloc[i - lookback:i + lookback + 1]['low'].min():
                df.at[df.index[i], 'swing_low'] = True
        
        self.logger.info(f"Identified {df['swing_high'].sum()} swing highs and {df['swing_low'].sum()} swing lows")
        return df
    
    def identify_market_structure(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Identify market structure (bullish/bearish/ranging)
        
        Args:
            df: DataFrame with OHLC data and swing points
            
        Returns:
            Dictionary with market structure information
        """
        if 'swing_high' not in df.columns:
            df = self.identify_swing_points(df)
        
        # Get swing points
        swing_highs = df[df['swing_high']]['high'].values
        swing_lows = df[df['swing_low']]['low'].values
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                'trend': 'RANGING',
                'structure': 'NEUTRAL',
                'strength': 0
            }
        
        # Check for higher highs and higher lows (bullish structure)
        recent_highs = swing_highs[-3:]
        recent_lows = swing_lows[-3:]
        
        higher_highs = all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs)))
        higher_lows = all(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows)))
        
        # Check for lower highs and lower lows (bearish structure)
        lower_highs = all(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs)))
        lower_lows = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows)))
        
        if higher_highs and higher_lows:
            trend = 'BULLISH'
            strength = 2
        elif lower_highs and lower_lows:
            trend = 'BEARISH'
            strength = 2
        elif higher_highs or higher_lows:
            trend = 'BULLISH'
            strength = 1
        elif lower_highs or lower_lows:
            trend = 'BEARISH'
            strength = 1
        else:
            trend = 'RANGING'
            strength = 0
        
        return {
            'trend': trend,
            'structure': 'STRONG' if strength == 2 else 'WEAK' if strength == 1 else 'NEUTRAL',
            'strength': strength,
            'last_swing_high': swing_highs[-1] if len(swing_highs) > 0 else None,
            'last_swing_low': swing_lows[-1] if len(swing_lows) > 0 else None
        }
    
    def identify_order_blocks(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """
        Identify bullish and bearish order blocks
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Tuple of (bullish_order_blocks, bearish_order_blocks)
        """
        bullish_obs = []
        bearish_obs = []
        
        # Look for order blocks (last down candle before strong up move, and vice versa)
        for i in range(1, len(df) - 1):
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            next_candle = df.iloc[i + 1]
            
            # Bullish Order Block: bearish candle followed by strong bullish move
            if (prev['close'] < prev['open'] and  # Previous candle is bearish
                next_candle['close'] > next_candle['open'] and  # Next candle is bullish
                (next_candle['close'] - next_candle['open']) > (prev['open'] - prev['close']) * 1.5):  # Strong move
                
                bullish_obs.append({
                    'index': i - 1,
                    'time': df.iloc[i - 1]['time'],
                    'high': prev['high'],
                    'low': prev['low'],
                    'type': 'BULLISH_OB'
                })
            
            # Bearish Order Block: bullish candle followed by strong bearish move
            if (prev['close'] > prev['open'] and  # Previous candle is bullish
                next_candle['close'] < next_candle['open'] and  # Next candle is bearish
                (next_candle['open'] - next_candle['close']) > (prev['close'] - prev['open']) * 1.5):  # Strong move
                
                bearish_obs.append({
                    'index': i - 1,
                    'time': df.iloc[i - 1]['time'],
                    'high': prev['high'],
                    'low': prev['low'],
                    'type': 'BEARISH_OB'
                })
        
        self.logger.info(f"Identified {len(bullish_obs)} bullish and {len(bearish_obs)} bearish order blocks")
        return bullish_obs, bearish_obs
    
    def identify_fair_value_gaps(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """
        Identify Fair Value Gaps (FVG)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Tuple of (bullish_fvgs, bearish_fvgs)
        """
        bullish_fvgs = []
        bearish_fvgs = []
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i - 2]
            candle2 = df.iloc[i - 1]
            candle3 = df.iloc[i]
            
            # Bullish FVG: gap between candle1 high and candle3 low
            if candle3['low'] > candle1['high']:
                gap_size = candle3['low'] - candle1['high']
                if gap_size > self.fvg_min_gap:
                    bullish_fvgs.append({
                        'index': i,
                        'time': df.iloc[i]['time'],
                        'top': candle3['low'],
                        'bottom': candle1['high'],
                        'size': gap_size,
                        'type': 'BULLISH_FVG'
                    })
            
            # Bearish FVG: gap between candle1 low and candle3 high
            if candle3['high'] < candle1['low']:
                gap_size = candle1['low'] - candle3['high']
                if gap_size > self.fvg_min_gap:
                    bearish_fvgs.append({
                        'index': i,
                        'time': df.iloc[i]['time'],
                        'top': candle1['low'],
                        'bottom': candle3['high'],
                        'size': gap_size,
                        'type': 'BEARISH_FVG'
                    })
        
        self.logger.info(f"Identified {len(bullish_fvgs)} bullish and {len(bearish_fvgs)} bearish FVGs")
        return bullish_fvgs, bearish_fvgs
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Perform complete SMC analysis
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with all SMC analysis results
        """
        self.logger.info("Starting SMC analysis...")
        
        # Identify swing points
        df = self.identify_swing_points(df)
        
        # Identify market structure
        market_structure = self.identify_market_structure(df)
        
        # Identify order blocks
        bullish_obs, bearish_obs = self.identify_order_blocks(df)
        
        # Identify fair value gaps
        bullish_fvgs, bearish_fvgs = self.identify_fair_value_gaps(df)
        
        # Get most recent important levels
        recent_bullish_ob = bullish_obs[-1] if bullish_obs else None
        recent_bearish_ob = bearish_obs[-1] if bearish_obs else None
        recent_bullish_fvg = bullish_fvgs[-1] if bullish_fvgs else None
        recent_bearish_fvg = bearish_fvgs[-1] if bearish_fvgs else None
        
        results = {
            'market_structure': market_structure,
            'order_blocks': {
                'bullish': bullish_obs,
                'bearish': bearish_obs,
                'recent_bullish': recent_bullish_ob,
                'recent_bearish': recent_bearish_ob
            },
            'fair_value_gaps': {
                'bullish': bullish_fvgs,
                'bearish': bearish_fvgs,
                'recent_bullish': recent_bullish_fvg,
                'recent_bearish': recent_bearish_fvg
            },
            'swing_points': {
                'highs': df[df['swing_high']].to_dict('records'),
                'lows': df[df['swing_low']].to_dict('records')
            }
        }
        
        self.logger.info("SMC analysis complete")
        return results
    
    def get_trading_signal(self, analysis: Dict, current_price: float) -> Optional[str]:
        """
        Generate trading signal based on SMC analysis
        
        Args:
            analysis: SMC analysis results
            current_price: Current market price
            
        Returns:
            'BUY', 'SELL', or None
        """
        market_structure = analysis['market_structure']
        trend = market_structure['trend']
        strength = market_structure['strength']
        
        # Strong trend required for signal
        if strength < 1:
            return None
        
        recent_bullish_ob = analysis['order_blocks']['recent_bullish']
        recent_bearish_ob = analysis['order_blocks']['recent_bearish']
        recent_bullish_fvg = analysis['fair_value_gaps']['recent_bullish']
        recent_bearish_fvg = analysis['fair_value_gaps']['recent_bearish']
        
        # Buy signal: bullish trend + price near bullish OB or FVG
        if trend == 'BULLISH':
            if recent_bullish_ob:
                if recent_bullish_ob['low'] <= current_price <= recent_bullish_ob['high']:
                    self.logger.info("BUY signal: Price in bullish order block")
                    return 'BUY'
            
            if recent_bullish_fvg:
                if recent_bullish_fvg['bottom'] <= current_price <= recent_bullish_fvg['top']:
                    self.logger.info("BUY signal: Price in bullish FVG")
                    return 'BUY'
        
        # Sell signal: bearish trend + price near bearish OB or FVG
        elif trend == 'BEARISH':
            if recent_bearish_ob:
                if recent_bearish_ob['low'] <= current_price <= recent_bearish_ob['high']:
                    self.logger.info("SELL signal: Price in bearish order block")
                    return 'SELL'
            
            if recent_bearish_fvg:
                if recent_bearish_fvg['bottom'] <= current_price <= recent_bearish_fvg['top']:
                    self.logger.info("SELL signal: Price in bearish FVG")
                    return 'SELL'
        
        return None
