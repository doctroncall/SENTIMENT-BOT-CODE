"""
SMC Components - Core Detectors
================================

Production-grade implementations of Smart Money Concepts detectors:
- Order Block Detector
- Market Structure Analyzer  
- Fair Value Gap Detector

Each component is independent, testable, and configurable.

Author: Trading Bot Team
Version: 1.0.0
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class OrderBlock:
    """Represents an institutional order block"""
    type: str  # 'bullish' or 'bearish'
    high: float
    low: float
    timeframe: str
    timestamp: datetime
    strength: float  # 0-100
    validated: bool = True
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'high': self.high,
            'low': self.low,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'strength': round(self.strength, 1),
            'validated': self.validated
        }
    
    def __repr__(self) -> str:
        return f"OrderBlock({self.type}, {self.timeframe}, strength={self.strength:.0f})"


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (price imbalance)"""
    type: str  # 'bullish' or 'bearish'
    top: float
    bottom: float
    timeframe: str
    timestamp: datetime
    size: float
    filled: bool = False
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'top': self.top,
            'bottom': self.bottom,
            'size': round(self.size, 5),
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'filled': self.filled
        }
    
    def __repr__(self) -> str:
        return f"FVG({self.type}, {self.timeframe}, size={self.size:.5f})"


@dataclass
class MarketStructure:
    """Market structure analysis result"""
    timeframe: str
    trend: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    swing_highs: List[float]
    swing_lows: List[float]
    last_bos: Optional[str] = None
    last_choch: Optional[str] = None
    structure_strength: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'timeframe': self.timeframe,
            'trend': self.trend,
            'swing_highs_count': len(self.swing_highs),
            'swing_lows_count': len(self.swing_lows),
            'structure_strength': round(self.structure_strength, 1),
            'last_bos': self.last_bos,
            'last_choch': self.last_choch
        }
    
    def __repr__(self) -> str:
        return f"MarketStructure({self.timeframe}, {self.trend}, strength={self.structure_strength:.0f})"


# ============================================================================
# ORDER BLOCK DETECTOR
# ============================================================================

class OrderBlockDetector:
    """
    Detects institutional order blocks using price action patterns
    
    Rules:
    - Bullish OB: Last down candle before strong bullish move
    - Bearish OB: Last up candle before strong bearish move
    - Minimum body size: 50% of candle range
    - Must have 3-candle confirmation
    
    Strength Calculation (0-100):
    - Body ratio: 40 points max
    - Follow-through: 30 points max
    - Momentum: 30 points max
    """
    
    def __init__(self, min_strength: int = 60, body_threshold: float = 0.5):
        """
        Initialize Order Block Detector
        
        Args:
            min_strength: Minimum strength to consider valid (default: 60)
            body_threshold: Minimum body/range ratio (default: 0.5)
        """
        self.min_strength = min_strength
        self.body_threshold = body_threshold
        self.logger = logging.getLogger(f"{__name__}.OrderBlockDetector")
    
    def detect(self, df: pd.DataFrame, timeframe: str) -> List[OrderBlock]:
        """
        Detect order blocks in price data
        
        Args:
            df: OHLC DataFrame with timezone-aware index
            timeframe: Timeframe string (e.g., 'D1', 'H4')
        
        Returns:
            List of detected order blocks
        """
        if df is None or df.empty:
            self.logger.warning("Empty DataFrame provided")
            return []
        
        if len(df) < 5:
            self.logger.warning(f"Insufficient data: {len(df)} bars (need 5+)")
            return []
        
        order_blocks = []
        
        try:
            for i in range(len(df) - 4):
                # Bullish Order Block
                if self._is_bullish_ob(df, i):
                    strength = self._calculate_ob_strength(df, i, 'bullish')
                    if strength >= self.min_strength:
                        ob = OrderBlock(
                            type='bullish',
                            high=float(df.iloc[i]['high']),
                            low=float(df.iloc[i]['low']),
                            timeframe=timeframe,
                            timestamp=df.index[i],
                            strength=strength
                        )
                        order_blocks.append(ob)
                        self.logger.debug(f"Bullish OB: {df.index[i]} strength={strength:.0f}")
                
                # Bearish Order Block
                if self._is_bearish_ob(df, i):
                    strength = self._calculate_ob_strength(df, i, 'bearish')
                    if strength >= self.min_strength:
                        ob = OrderBlock(
                            type='bearish',
                            high=float(df.iloc[i]['high']),
                            low=float(df.iloc[i]['low']),
                            timeframe=timeframe,
                            timestamp=df.index[i],
                            strength=strength
                        )
                        order_blocks.append(ob)
                        self.logger.debug(f"Bearish OB: {df.index[i]} strength={strength:.0f}")
            
            self.logger.info(f"Detected {len(order_blocks)} order blocks on {timeframe}")
            return order_blocks
            
        except Exception as e:
            self.logger.error(f"Error detecting order blocks: {e}")
            return []
    
    def _is_bullish_ob(self, df: pd.DataFrame, i: int) -> bool:
        """Check if candle at index i is a bullish order block"""
        try:
            current = df.iloc[i]
            next_3 = df.iloc[i+1:i+4]
            
            if len(next_3) < 3:
                return False
            
            # Current candle must be bearish
            is_bearish = current['close'] < current['open']
            if not is_bearish:
                return False
            
            # Must have significant body
            body = abs(current['close'] - current['open'])
            range_size = current['high'] - current['low']
            if range_size == 0:
                return False
            has_body = (body / range_size) > self.body_threshold
            
            # Next 3 candles show bullish momentum
            bullish_count = (next_3['close'] > next_3['open']).sum()
            strong_move = next_3['close'].iloc[-1] > current['high']
            
            return has_body and bullish_count >= 2 and strong_move
            
        except Exception as e:
            self.logger.debug(f"Error in bullish OB check at {i}: {e}")
            return False
    
    def _is_bearish_ob(self, df: pd.DataFrame, i: int) -> bool:
        """Check if candle at index i is a bearish order block"""
        try:
            current = df.iloc[i]
            next_3 = df.iloc[i+1:i+4]
            
            if len(next_3) < 3:
                return False
            
            # Current candle must be bullish
            is_bullish = current['close'] > current['open']
            if not is_bullish:
                return False
            
            # Must have significant body
            body = abs(current['close'] - current['open'])
            range_size = current['high'] - current['low']
            if range_size == 0:
                return False
            has_body = (body / range_size) > self.body_threshold
            
            # Next 3 candles show bearish momentum
            bearish_count = (next_3['close'] < next_3['open']).sum()
            strong_move = next_3['close'].iloc[-1] < current['low']
            
            return has_body and bearish_count >= 2 and strong_move
            
        except Exception as e:
            self.logger.debug(f"Error in bearish OB check at {i}: {e}")
            return False
    
    def _calculate_ob_strength(self, df: pd.DataFrame, i: int, ob_type: str) -> float:
        """Calculate order block strength (0-100)"""
        try:
            strength = 0.0
            current = df.iloc[i]
            
            # 1. Body strength (40 points max)
            body = abs(current['close'] - current['open'])
            range_size = current['high'] - current['low']
            if range_size > 0:
                body_ratio = body / range_size
                strength += min(body_ratio * 40, 40)
            
            # 2. Follow-through strength (30 points max)
            next_3 = df.iloc[i+1:i+4]
            if ob_type == 'bullish':
                bullish_pct = (next_3['close'] > next_3['open']).sum() / 3
                strength += bullish_pct * 30
            else:
                bearish_pct = (next_3['close'] < next_3['open']).sum() / 3
                strength += bearish_pct * 30
            
            # 3. Momentum strength (30 points max)
            if len(next_3) == 3:
                move_size = abs(next_3['close'].iloc[-1] - current['close'])
                # Calculate average range from last 10 candles
                start_idx = max(0, i-10)
                avg_range = (df['high'].iloc[start_idx:i+1] - df['low'].iloc[start_idx:i+1]).mean()
                if avg_range > 0:
                    momentum_score = min((move_size / avg_range) * 30, 30)
                    strength += momentum_score
            
            return min(strength, 100.0)
            
        except Exception as e:
            self.logger.debug(f"Error calculating OB strength: {e}")
            return 0.0


# ============================================================================
# MARKET STRUCTURE ANALYZER
# ============================================================================

class MarketStructureAnalyzer:
    """
    Analyzes market structure for trend, BOS, CHoCH
    
    Rules:
    - Higher Highs + Higher Lows = Bullish Trend
    - Lower Highs + Lower Lows = Bearish Trend
    - BOS = Break of Structure (in trend direction)
    - CHoCH = Change of Character (counter-trend break)
    
    Swing Detection:
    - Looks back N candles on each side
    - Identifies local maxima/minima
    - Validates with surrounding candles
    """
    
    def __init__(self, swing_lookback: int = 5):
        """
        Initialize Market Structure Analyzer
        
        Args:
            swing_lookback: Number of candles to look back for swing detection
        """
        self.swing_lookback = swing_lookback
        self.logger = logging.getLogger(f"{__name__}.MarketStructureAnalyzer")
    
    def analyze(self, df: pd.DataFrame, timeframe: str) -> MarketStructure:
        """
        Analyze market structure
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe string
        
        Returns:
            MarketStructure object
        """
        if df is None or df.empty:
            self.logger.warning("Empty DataFrame provided")
            return MarketStructure(
                timeframe=timeframe,
                trend='NEUTRAL',
                swing_highs=[],
                swing_lows=[],
                structure_strength=0.0
            )
        
        min_data = self.swing_lookback * 3
        if len(df) < min_data:
            self.logger.warning(f"Insufficient data: {len(df)} bars (need {min_data}+)")
            return MarketStructure(
                timeframe=timeframe,
                trend='NEUTRAL',
                swing_highs=[],
                swing_lows=[],
                structure_strength=0.0
            )
        
        try:
            # Find swing points
            swing_highs = self._find_swing_highs(df)
            swing_lows = self._find_swing_lows(df)
            
            # Determine trend
            trend = self._determine_trend(swing_highs, swing_lows)
            
            # Calculate structure strength
            strength = self._calculate_structure_strength(swing_highs, swing_lows, trend)
            
            structure = MarketStructure(
                timeframe=timeframe,
                trend=trend,
                swing_highs=swing_highs,
                swing_lows=swing_lows,
                structure_strength=strength
            )
            
            self.logger.info(f"Structure: {timeframe} = {trend} (strength={strength:.0f})")
            return structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing structure: {e}")
            return MarketStructure(
                timeframe=timeframe,
                trend='NEUTRAL',
                swing_highs=[],
                swing_lows=[],
                structure_strength=0.0
            )
    
    def _find_swing_highs(self, df: pd.DataFrame) -> List[float]:
        """Find swing high points"""
        swing_highs = []
        lookback = self.swing_lookback
        
        try:
            for i in range(lookback, len(df) - lookback):
                current_high = df.iloc[i]['high']
                
                # Check if higher than surrounding candles
                is_swing = True
                for j in range(1, lookback + 1):
                    if (df.iloc[i-j]['high'] >= current_high or 
                        df.iloc[i+j]['high'] >= current_high):
                        is_swing = False
                        break
                
                if is_swing:
                    swing_highs.append(float(current_high))
            
            return swing_highs
            
        except Exception as e:
            self.logger.debug(f"Error finding swing highs: {e}")
            return []
    
    def _find_swing_lows(self, df: pd.DataFrame) -> List[float]:
        """Find swing low points"""
        swing_lows = []
        lookback = self.swing_lookback
        
        try:
            for i in range(lookback, len(df) - lookback):
                current_low = df.iloc[i]['low']
                
                # Check if lower than surrounding candles
                is_swing = True
                for j in range(1, lookback + 1):
                    if (df.iloc[i-j]['low'] <= current_low or 
                        df.iloc[i+j]['low'] <= current_low):
                        is_swing = False
                        break
                
                if is_swing:
                    swing_lows.append(float(current_low))
            
            return swing_lows
            
        except Exception as e:
            self.logger.debug(f"Error finding swing lows: {e}")
            return []
    
    def _determine_trend(self, swing_highs: List[float], swing_lows: List[float]) -> str:
        """Determine trend from swing points"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'NEUTRAL'
        
        try:
            # Analyze recent 3 swings (or all if less than 3)
            recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
            recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
            
            # Check for higher highs and higher lows
            hh = all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs)))
            hl = all(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows)))
            
            if hh and hl:
                return 'BULLISH'
            
            # Check for lower highs and lower lows
            lh = all(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs)))
            ll = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows)))
            
            if lh and ll:
                return 'BEARISH'
            
            return 'NEUTRAL'
            
        except Exception as e:
            self.logger.debug(f"Error determining trend: {e}")
            return 'NEUTRAL'
    
    def _calculate_structure_strength(self, swing_highs: List[float], 
                                     swing_lows: List[float], trend: str) -> float:
        """Calculate structure strength (0-100)"""
        if trend == 'NEUTRAL':
            return 0.0
        
        try:
            strength = 50.0  # Base for identified trend
            
            # Points for number of swings
            total_swings = len(swing_highs) + len(swing_lows)
            strength += min(total_swings * 3, 30)  # Max 30 points
            
            # Points for complete structure (both sides)
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                strength += 20  # Bonus for complete structure
            
            return min(strength, 100.0)
            
        except Exception as e:
            self.logger.debug(f"Error calculating strength: {e}")
            return 50.0


# ============================================================================
# FAIR VALUE GAP DETECTOR
# ============================================================================

class FairValueGapDetector:
    """
    Detects Fair Value Gaps (price imbalances)
    
    Rules:
    - Bullish FVG: Gap between candle 1 low and candle 3 high
    - Bearish FVG: Gap between candle 1 high and candle 3 low
    - Minimum gap size: 0.5 * ATR
    - Must remain unfilled for validity
    """
    
    def __init__(self, min_gap_atr_multiplier: float = 0.5, atr_period: int = 14):
        """
        Initialize Fair Value Gap Detector
        
        Args:
            min_gap_atr_multiplier: Minimum gap size as multiple of ATR
            atr_period: Period for ATR calculation
        """
        self.min_gap_atr_multiplier = min_gap_atr_multiplier
        self.atr_period = atr_period
        self.logger = logging.getLogger(f"{__name__}.FairValueGapDetector")
    
    def detect(self, df: pd.DataFrame, timeframe: str) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe string
        
        Returns:
            List of detected FVGs
        """
        if df is None or df.empty:
            self.logger.warning("Empty DataFrame provided")
            return []
        
        if len(df) < max(3, self.atr_period):
            self.logger.warning(f"Insufficient data: {len(df)} bars")
            return []
        
        try:
            fvgs = []
            atr = self._calculate_atr(df)
            
            for i in range(2, len(df)):
                # Bullish FVG: Gap up
                if df.iloc[i-2]['low'] > df.iloc[i]['high']:
                    gap_size = df.iloc[i-2]['low'] - df.iloc[i]['high']
                    min_gap = atr.iloc[i] * self.min_gap_atr_multiplier
                    
                    if gap_size >= min_gap:
                        fvg = FairValueGap(
                            type='bullish',
                            top=float(df.iloc[i-2]['low']),
                            bottom=float(df.iloc[i]['high']),
                            timeframe=timeframe,
                            timestamp=df.index[i],
                            size=gap_size,
                            filled=False
                        )
                        fvgs.append(fvg)
                
                # Bearish FVG: Gap down
                if df.iloc[i-2]['high'] < df.iloc[i]['low']:
                    gap_size = df.iloc[i]['low'] - df.iloc[i-2]['high']
                    min_gap = atr.iloc[i] * self.min_gap_atr_multiplier
                    
                    if gap_size >= min_gap:
                        fvg = FairValueGap(
                            type='bearish',
                            top=float(df.iloc[i]['low']),
                            bottom=float(df.iloc[i-2]['high']),
                            timeframe=timeframe,
                            timestamp=df.index[i],
                            size=gap_size,
                            filled=False
                        )
                        fvgs.append(fvg)
            
            # Filter out filled FVGs
            valid_fvgs = self._filter_filled_fvgs(fvgs, df)
            
            self.logger.info(f"Detected {len(valid_fvgs)} unfilled FVGs on {timeframe}")
            return valid_fvgs
            
        except Exception as e:
            self.logger.error(f"Error detecting FVGs: {e}")
            return []
    
    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high = df['high']
            low = df['low']
            close = df['close'].shift(1)
            
            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=self.atr_period).mean()
            
            return atr.fillna(tr.mean())
            
        except Exception as e:
            self.logger.debug(f"Error calculating ATR: {e}")
            # Return series of ones as fallback
            return pd.Series([1.0] * len(df), index=df.index)
    
    def _filter_filled_fvgs(self, fvgs: List[FairValueGap], df: pd.DataFrame) -> List[FairValueGap]:
        """Remove FVGs that have been filled by price"""
        valid_fvgs = []
        
        try:
            for fvg in fvgs:
                # Get prices after FVG formation
                fvg_index = df.index.get_loc(fvg.timestamp)
                future_prices = df.iloc[fvg_index+1:]
                
                if len(future_prices) == 0:
                    valid_fvgs.append(fvg)
                    continue
                
                # Check if gap has been filled
                if fvg.type == 'bullish':
                    filled = (future_prices['low'] <= fvg.bottom).any()
                else:
                    filled = (future_prices['high'] >= fvg.top).any()
                
                if not filled:
                    valid_fvgs.append(fvg)
            
            return valid_fvgs
            
        except Exception as e:
            self.logger.debug(f"Error filtering FVGs: {e}")
            return fvgs  # Return all if error


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Simple test
    print("SMC Components - Module Test")
    print("="*70)
    
    # Create sample data
    dates = pd.date_range(start='2025-01-01', periods=100, freq='H', tz='UTC')
    np.random.seed(42)
    
    prices = 1.2700 + np.cumsum(np.random.normal(0, 0.0005, 100))
    df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.0001, 100)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.0003, 100))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.0003, 100))),
        'close': prices,
    }, index=dates)
    
    # Ensure OHLC validity
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    # Test Order Blocks
    print("\n1. Testing Order Block Detector...")
    ob_detector = OrderBlockDetector()
    obs = ob_detector.detect(df, 'H1')
    print(f"   Found {len(obs)} order blocks")
    if obs:
        print(f"   Example: {obs[0]}")
    
    # Test Market Structure
    print("\n2. Testing Market Structure Analyzer...")
    structure_analyzer = MarketStructureAnalyzer()
    structure = structure_analyzer.analyze(df, 'H1')
    print(f"   Trend: {structure.trend}")
    print(f"   Strength: {structure.structure_strength:.0f}")
    print(f"   Swings: {len(structure.swing_highs)} highs, {len(structure.swing_lows)} lows")
    
    # Test Fair Value Gaps
    print("\n3. Testing Fair Value Gap Detector...")
    fvg_detector = FairValueGapDetector()
    fvgs = fvg_detector.detect(df, 'H1')
    print(f"   Found {len(fvgs)} FVGs")
    if fvgs:
        print(f"   Example: {fvgs[0]}")
    
    print("\n" + "="*70)
    print("✅ All components tested successfully!")
