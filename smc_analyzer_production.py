"""
Production-Grade SMC Analysis Engine
=====================================

A robust, accurate SMC (Smart Money Concepts) analysis system
designed for production use with institutional-grade standards.

Author: Trading System Architect
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class BiasDirection(Enum):
    """Trading bias direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ConfidenceLevel(Enum):
    """Confidence level classification"""
    HIGH = "HIGH"       # 75+
    MEDIUM = "MEDIUM"   # 55-74
    LOW = "LOW"         # 40-54
    NEUTRAL = "NEUTRAL" # <40


@dataclass
class OrderBlock:
    """Represents a Smart Money order block"""
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
            'timestamp': self.timestamp.isoformat(),
            'strength': self.strength
        }


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (imbalance)"""
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
            'size': self.size,
            'timeframe': self.timeframe,
            'filled': self.filled
        }


@dataclass
class MarketStructure:
    """Market structure analysis result"""
    timeframe: str
    trend: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    swing_highs: List[float]
    swing_lows: List[float]
    last_bos: Optional[str] = None  # Break of Structure
    last_choch: Optional[str] = None  # Change of Character
    structure_strength: float = 0.0  # 0-100


@dataclass
class Signal:
    """Individual trading signal"""
    type: str  # 'order_block', 'fvg', 'structure', etc.
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: float  # 0-100
    timeframe: str
    confidence: float  # 0-100
    details: dict = field(default_factory=dict)


@dataclass
class Bias:
    """Final trading bias"""
    direction: BiasDirection
    confidence: float  # 0-100
    confidence_level: ConfidenceLevel
    bullish_score: float
    bearish_score: float
    signals: List[Signal] = field(default_factory=list)
    
    @classmethod
    def neutral(cls) -> 'Bias':
        """Create a neutral bias"""
        return cls(
            direction=BiasDirection.NEUTRAL,
            confidence=0.0,
            confidence_level=ConfidenceLevel.NEUTRAL,
            bullish_score=0.0,
            bearish_score=0.0
        )


# ============================================================================
# SMC DETECTORS
# ============================================================================

class OrderBlockDetector:
    """
    Detects institutional order blocks using price action patterns
    
    Rules:
    - Bullish OB: Last down candle before strong bullish move
    - Bearish OB: Last up candle before strong bearish move
    - Minimum body size: 50% of range
    - Must have follow-through confirmation
    """
    
    def __init__(self, min_strength: int = 60, body_threshold: float = 0.5):
        self.min_strength = min_strength
        self.body_threshold = body_threshold
        self.logger = logging.getLogger(f"{__name__}.OrderBlockDetector")
    
    def detect(self, df: pd.DataFrame, timeframe: str) -> List[OrderBlock]:
        """Detect order blocks in the given data"""
        if len(df) < 5:
            self.logger.warning(f"Insufficient data for OB detection: {len(df)} bars")
            return []
        
        order_blocks = []
        
        for i in range(len(df) - 4):
            # Bullish Order Block
            if self._is_bullish_ob(df, i):
                strength = self._calculate_ob_strength(df, i, 'bullish')
                if strength >= self.min_strength:
                    ob = OrderBlock(
                        type='bullish',
                        high=df.iloc[i]['high'],
                        low=df.iloc[i]['low'],
                        timeframe=timeframe,
                        timestamp=df.index[i],
                        strength=strength
                    )
                    order_blocks.append(ob)
                    self.logger.debug(f"Bullish OB detected at {df.index[i]} (strength={strength:.0f})")
            
            # Bearish Order Block
            if self._is_bearish_ob(df, i):
                strength = self._calculate_ob_strength(df, i, 'bearish')
                if strength >= self.min_strength:
                    ob = OrderBlock(
                        type='bearish',
                        high=df.iloc[i]['high'],
                        low=df.iloc[i]['low'],
                        timeframe=timeframe,
                        timestamp=df.index[i],
                        strength=strength
                    )
                    order_blocks.append(ob)
                    self.logger.debug(f"Bearish OB detected at {df.index[i]} (strength={strength:.0f})")
        
        self.logger.info(f"Detected {len(order_blocks)} order blocks on {timeframe}")
        return order_blocks
    
    def _is_bullish_ob(self, df: pd.DataFrame, i: int) -> bool:
        """Check if index i represents a bullish order block"""
        current = df.iloc[i]
        next_3 = df.iloc[i+1:i+4]
        
        if len(next_3) < 3:
            return False
        
        # Current candle is bearish
        is_bearish = current['close'] < current['open']
        
        # Has significant body
        body = abs(current['close'] - current['open'])
        range_size = current['high'] - current['low']
        has_body = (body / range_size) > self.body_threshold if range_size > 0 else False
        
        # Next 3 candles show bullish momentum
        bullish_count = (next_3['close'] > next_3['open']).sum()
        strong_move = next_3['close'].iloc[-1] > current['high']
        
        return is_bearish and has_body and bullish_count >= 2 and strong_move
    
    def _is_bearish_ob(self, df: pd.DataFrame, i: int) -> bool:
        """Check if index i represents a bearish order block"""
        current = df.iloc[i]
        next_3 = df.iloc[i+1:i+4]
        
        if len(next_3) < 3:
            return False
        
        # Current candle is bullish
        is_bullish = current['close'] > current['open']
        
        # Has significant body
        body = abs(current['close'] - current['open'])
        range_size = current['high'] - current['low']
        has_body = (body / range_size) > self.body_threshold if range_size > 0 else False
        
        # Next 3 candles show bearish momentum
        bearish_count = (next_3['close'] < next_3['open']).sum()
        strong_move = next_3['close'].iloc[-1] < current['low']
        
        return is_bullish and has_body and bearish_count >= 2 and strong_move
    
    def _calculate_ob_strength(self, df: pd.DataFrame, i: int, ob_type: str) -> float:
        """Calculate order block strength (0-100)"""
        strength = 0.0
        
        # Base strength from body size
        current = df.iloc[i]
        body = abs(current['close'] - current['open'])
        range_size = current['high'] - current['low']
        body_ratio = (body / range_size) if range_size > 0 else 0
        strength += body_ratio * 40  # Max 40 points
        
        # Strength from follow-through
        next_3 = df.iloc[i+1:i+4]
        if ob_type == 'bullish':
            bullish_pct = (next_3['close'] > next_3['open']).sum() / 3
            strength += bullish_pct * 30  # Max 30 points
        else:
            bearish_pct = (next_3['close'] < next_3['open']).sum() / 3
            strength += bearish_pct * 30  # Max 30 points
        
        # Strength from momentum
        move_size = abs(next_3['close'].iloc[-1] - current['close'])
        avg_range = df['high'].iloc[max(0, i-10):i+1].sub(df['low'].iloc[max(0, i-10):i+1]).mean()
        if avg_range > 0:
            momentum_score = min((move_size / avg_range) * 30, 30)
            strength += momentum_score  # Max 30 points
        
        return min(strength, 100)


class MarketStructureAnalyzer:
    """
    Analyzes market structure for trend, BOS, CHoCH
    
    Rules:
    - Higher Highs + Higher Lows = Uptrend
    - Lower Highs + Lower Lows = Downtrend
    - BOS = Break of structure in trend direction
    - CHoCH = Change of character (counter-trend break)
    """
    
    def __init__(self, swing_lookback: int = 5):
        self.swing_lookback = swing_lookback
        self.logger = logging.getLogger(f"{__name__}.MarketStructureAnalyzer")
    
    def analyze(self, df: pd.DataFrame, timeframe: str) -> MarketStructure:
        """Analyze market structure"""
        if len(df) < self.swing_lookback * 3:
            self.logger.warning(f"Insufficient data for structure analysis: {len(df)} bars")
            return MarketStructure(
                timeframe=timeframe,
                trend='NEUTRAL',
                swing_highs=[],
                swing_lows=[]
            )
        
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
        
        self.logger.info(f"Market structure on {timeframe}: {trend} (strength={strength:.0f})")
        return structure
    
    def _find_swing_highs(self, df: pd.DataFrame) -> List[float]:
        """Find swing high points"""
        swing_highs = []
        lookback = self.swing_lookback
        
        for i in range(lookback, len(df) - lookback):
            current_high = df.iloc[i]['high']
            
            # Check if higher than surrounding candles
            is_swing_high = True
            for j in range(1, lookback + 1):
                if (df.iloc[i-j]['high'] >= current_high or 
                    df.iloc[i+j]['high'] >= current_high):
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append(current_high)
        
        return swing_highs
    
    def _find_swing_lows(self, df: pd.DataFrame) -> List[float]:
        """Find swing low points"""
        swing_lows = []
        lookback = self.swing_lookback
        
        for i in range(lookback, len(df) - lookback):
            current_low = df.iloc[i]['low']
            
            # Check if lower than surrounding candles
            is_swing_low = True
            for j in range(1, lookback + 1):
                if (df.iloc[i-j]['low'] <= current_low or 
                    df.iloc[i+j]['low'] <= current_low):
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append(current_low)
        
        return swing_lows
    
    def _determine_trend(self, swing_highs: List[float], swing_lows: List[float]) -> str:
        """Determine trend from swing points"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'NEUTRAL'
        
        # Analyze last 3 swing points
        recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
        recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
        
        # Check for higher highs and higher lows
        if len(recent_highs) >= 2:
            hh = all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs)))
        else:
            hh = False
        
        if len(recent_lows) >= 2:
            hl = all(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows)))
        else:
            hl = False
        
        if hh and hl:
            return 'BULLISH'
        
        # Check for lower highs and lower lows
        if len(recent_highs) >= 2:
            lh = all(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs)))
        else:
            lh = False
        
        if len(recent_lows) >= 2:
            ll = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows)))
        else:
            ll = False
        
        if lh and ll:
            return 'BEARISH'
        
        return 'NEUTRAL'
    
    def _calculate_structure_strength(self, swing_highs: List[float], 
                                     swing_lows: List[float], trend: str) -> float:
        """Calculate structure strength (0-100)"""
        if trend == 'NEUTRAL':
            return 0.0
        
        strength = 50.0  # Base strength for identified trend
        
        # Add strength for number of confirming swings
        recent_highs = swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs
        recent_lows = swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows
        
        swing_count = len(recent_highs) + len(recent_lows)
        strength += min(swing_count * 5, 30)  # Max 30 points
        
        # Add strength for trend consistency
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            strength += 20  # Bonus for complete structure
        
        return min(strength, 100)


# ============================================================================
# BIAS CALCULATION ENGINE
# ============================================================================

class BiasCalculator:
    """
    Calculates final trading bias from multiple signals with weighted scoring
    """
    
    # Signal weights (must sum to 1.0)
    SIGNAL_WEIGHTS = {
        'order_block': 0.30,
        'market_structure': 0.35,
        'fvg': 0.20,
        'momentum': 0.10,
        'volume': 0.05
    }
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        'HIGH': 75,
        'MEDIUM': 55,
        'LOW': 40
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.BiasCalculator")
    
    def calculate(self, signals: List[Signal]) -> Bias:
        """Calculate final bias from signals"""
        if not signals:
            self.logger.warning("No signals provided for bias calculation")
            return Bias.neutral()
        
        bullish_score = 0.0
        bearish_score = 0.0
        max_possible = 0.0
        
        # Aggregate signals by type
        signals_by_type = self._group_signals_by_type(signals)
        
        # Calculate weighted scores
        for signal_type, signal_list in signals_by_type.items():
            weight = self.SIGNAL_WEIGHTS.get(signal_type, 0)
            if weight == 0:
                continue
            
            max_possible += weight * 100
            
            # Average signals of same type
            avg_strength = sum(s.strength for s in signal_list) / len(signal_list)
            bullish_signals = [s for s in signal_list if s.direction == 'BULLISH']
            bearish_signals = [s for s in signal_list if s.direction == 'BEARISH']
            
            if bullish_signals:
                bullish_strength = sum(s.strength for s in bullish_signals) / len(signal_list)
                bullish_score += weight * bullish_strength
            
            if bearish_signals:
                bearish_strength = sum(s.strength for s in bearish_signals) / len(signal_list)
                bearish_score += weight * bearish_strength
        
        # Normalize scores to percentage
        if max_possible > 0:
            bullish_pct = (bullish_score / max_possible) * 100
            bearish_pct = (bearish_score / max_possible) * 100
        else:
            bullish_pct = bearish_pct = 0.0
        
        # Determine bias and confidence
        if bullish_pct > bearish_pct and bullish_pct >= self.CONFIDENCE_THRESHOLDS['LOW']:
            direction = BiasDirection.BULLISH
            confidence = bullish_pct
        elif bearish_pct > bullish_pct and bearish_pct >= self.CONFIDENCE_THRESHOLDS['LOW']:
            direction = BiasDirection.BEARISH
            confidence = bearish_pct
        else:
            direction = BiasDirection.NEUTRAL
            confidence = max(bullish_pct, bearish_pct)
        
        # Determine confidence level
        if confidence >= self.CONFIDENCE_THRESHOLDS['HIGH']:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence >= self.CONFIDENCE_THRESHOLDS['MEDIUM']:
            confidence_level = ConfidenceLevel.MEDIUM
        elif confidence >= self.CONFIDENCE_THRESHOLDS['LOW']:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.NEUTRAL
        
        bias = Bias(
            direction=direction,
            confidence=confidence,
            confidence_level=confidence_level,
            bullish_score=bullish_pct,
            bearish_score=bearish_pct,
            signals=signals
        )
        
        self.logger.info(
            f"Bias calculated: {direction.value} "
            f"(confidence={confidence:.1f}%, level={confidence_level.value})"
        )
        
        return bias
    
    def _group_signals_by_type(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        """Group signals by type"""
        grouped = {}
        for signal in signals:
            if signal.type not in grouped:
                grouped[signal.type] = []
            grouped[signal.type].append(signal)
        return grouped


# ============================================================================
# MAIN SMC ANALYZER
# ============================================================================

class SMCAnalyzer:
    """
    Production-grade SMC analysis orchestrator
    
    Coordinates all SMC detectors and calculates final bias
    """
    
    def __init__(self):
        self.ob_detector = OrderBlockDetector()
        self.structure_analyzer = MarketStructureAnalyzer()
        self.bias_calculator = BiasCalculator()
        self.logger = logging.getLogger(f"{__name__}.SMCAnalyzer")
    
    def analyze(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Bias:
        """
        Analyze symbol using SMC concepts
        
        Args:
            symbol: Trading symbol (e.g., 'GBPUSD')
            data: Dictionary of {timeframe: DataFrame}
        
        Returns:
            Bias object with final trading direction and confidence
        """
        self.logger.info(f"{'='*70}")
        self.logger.info(f"Starting SMC analysis for {symbol}")
        self.logger.info(f"{'='*70}")
        
        try:
            # Validate input data
            if not self._validate_data(data):
                self.logger.error("Data validation failed")
                return Bias.neutral()
            
            # Collect signals from all timeframes
            all_signals = []
            
            for timeframe, df in data.items():
                self.logger.info(f"\n📊 Analyzing {timeframe}...")
                self.logger.info(f"{'-'*70}")
                
                try:
                    signals = self._analyze_timeframe(df, timeframe)
                    all_signals.extend(signals)
                    self.logger.info(f"✅ {timeframe}: {len(signals)} signals generated")
                except Exception as e:
                    self.logger.error(f"❌ {timeframe} analysis failed: {e}")
                    # Continue with other timeframes
                    continue
            
            if not all_signals:
                self.logger.error("No signals generated from any timeframe")
                return Bias.neutral()
            
            # Calculate final bias
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"Calculating final bias from {len(all_signals)} signals...")
            self.logger.info(f"{'='*70}")
            
            bias = self.bias_calculator.calculate(all_signals)
            
            # Validate result
            if not self._validate_bias(bias, all_signals):
                self.logger.warning("Bias validation failed - returning neutral")
                return Bias.neutral()
            
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"✅ SMC ANALYSIS COMPLETE")
            self.logger.info(f"{'='*70}")
            self.logger.info(f"Symbol: {symbol}")
            self.logger.info(f"Bias: {bias.direction.value}")
            self.logger.info(f"Confidence: {bias.confidence:.1f}%")
            self.logger.info(f"Level: {bias.confidence_level.value}")
            self.logger.info(f"Bullish Score: {bias.bullish_score:.1f}%")
            self.logger.info(f"Bearish Score: {bias.bearish_score:.1f}%")
            self.logger.info(f"{'='*70}\n")
            
            return bias
            
        except Exception as e:
            self.logger.exception(f"Critical error in SMC analysis: {e}")
            return Bias.neutral()
    
    def _analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> List[Signal]:
        """Analyze single timeframe and generate signals"""
        signals = []
        
        # 1. Order Blocks
        try:
            obs = self.ob_detector.detect(df, timeframe)
            for ob in obs:
                signal = Signal(
                    type='order_block',
                    direction='BULLISH' if ob.type == 'bullish' else 'BEARISH',
                    strength=ob.strength,
                    timeframe=timeframe,
                    confidence=ob.strength,
                    details={'order_block': ob.to_dict()}
                )
                signals.append(signal)
            self.logger.info(f"  Order Blocks: {len(obs)} detected")
        except Exception as e:
            self.logger.error(f"  Order Block detection failed: {e}")
        
        # 2. Market Structure
        try:
            structure = self.structure_analyzer.analyze(df, timeframe)
            if structure.trend != 'NEUTRAL':
                signal = Signal(
                    type='market_structure',
                    direction=structure.trend,
                    strength=structure.structure_strength,
                    timeframe=timeframe,
                    confidence=structure.structure_strength,
                    details={'trend': structure.trend}
                )
                signals.append(signal)
            self.logger.info(f"  Market Structure: {structure.trend} (strength={structure.structure_strength:.0f})")
        except Exception as e:
            self.logger.error(f"  Market structure analysis failed: {e}")
        
        # Add more SMC concepts here (FVG, liquidity zones, etc.)
        
        return signals
    
    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate input data quality"""
        if not data:
            self.logger.error("No data provided")
            return False
        
        for tf, df in data.items():
            if df is None or df.empty:
                self.logger.error(f"Empty data for {tf}")
                return False
            
            required_cols = ['open', 'high', 'low', 'close']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                self.logger.error(f"Missing columns for {tf}: {missing}")
                return False
            
            if len(df) < 30:
                self.logger.warning(f"Insufficient bars for {tf}: {len(df)}")
                return False
        
        return True
    
    def _validate_bias(self, bias: Bias, signals: List[Signal]) -> bool:
        """Validate bias result makes sense"""
        # High confidence should have multiple confirming signals
        if bias.confidence_level == ConfidenceLevel.HIGH:
            confirming = sum(1 for s in signals if s.direction == bias.direction.value)
            if confirming < 2:
                self.logger.warning(
                    f"High confidence ({bias.confidence:.1f}%) "
                    f"with only {confirming} confirming signals"
                )
                return False
        
        # Bias should have structure support
        if bias.direction != BiasDirection.NEUTRAL:
            has_structure = any(
                s.type == 'market_structure' and s.direction == bias.direction.value
                for s in signals
            )
            if not has_structure:
                self.logger.warning(
                    f"{bias.direction.value} bias without supporting structure"
                )
                # Don't fail, just warn
        
        return True


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SMC Analyzer - Production Grade Implementation")
    print("="*70 + "\n")
    
    # Example: Create sample data (in production, this comes from data_manager)
    dates = pd.date_range(start='2025-01-01', periods=100, freq='H', tz='UTC')
    
    # Simulate price data with trend
    np.random.seed(42)
    base_price = 1.2700
    trend = np.linspace(0, 0.01, 100)  # Uptrend
    noise = np.random.normal(0, 0.0005, 100)
    close_prices = base_price + trend + noise
    
    df_h1 = pd.DataFrame({
        'open': close_prices * (1 + np.random.normal(0, 0.0001, 100)),
        'high': close_prices * (1 + np.abs(np.random.normal(0, 0.0003, 100))),
        'low': close_prices * (1 - np.abs(np.random.normal(0, 0.0003, 100))),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Ensure OHLC relationships
    df_h1['high'] = df_h1[['open', 'high', 'close']].max(axis=1)
    df_h1['low'] = df_h1[['open', 'low', 'close']].min(axis=1)
    
    # Create multi-timeframe data
    data = {
        'H1': df_h1,
        'H4': df_h1.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    }
    
    # Run SMC analysis
    analyzer = SMCAnalyzer()
    bias = analyzer.analyze('GBPUSD', data)
    
    # Display results
    print("\n" + "="*70)
    print("FINAL ANALYSIS RESULT")
    print("="*70)
    print(f"Bias: {bias.direction.value}")
    print(f"Confidence: {bias.confidence:.1f}%")
    print(f"Confidence Level: {bias.confidence_level.value}")
    print(f"Bullish Score: {bias.bullish_score:.1f}%")
    print(f"Bearish Score: {bias.bearish_score:.1f}%")
    print(f"Total Signals: {len(bias.signals)}")
    print("="*70 + "\n")
    
    print("✅ Production-grade SMC analysis complete!")
