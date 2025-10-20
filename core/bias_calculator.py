"""
Bias Calculator - Weighted Scoring System
==========================================

Calculates final trading bias from multiple SMC signals using
weighted scoring, multi-timeframe confluence, and confidence levels.

Author: Trading Bot Team
Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMERATIONS
# ============================================================================

class BiasDirection(Enum):
    """Trading bias direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    
    def __str__(self) -> str:
        return self.value


class ConfidenceLevel(Enum):
    """Confidence level classification"""
    HIGH = "HIGH"       # 75+%
    MEDIUM = "MEDIUM"   # 55-74%
    LOW = "LOW"         # 40-54%
    NEUTRAL = "NEUTRAL" # <40%
    
    def __str__(self) -> str:
        return self.value


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Signal:
    """Individual trading signal from SMC component"""
    type: str  # 'order_block', 'market_structure', 'fvg', etc.
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: float  # 0-100
    timeframe: str
    confidence: float  # 0-100
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'direction': self.direction,
            'strength': round(self.strength, 1),
            'timeframe': self.timeframe,
            'confidence': round(self.confidence, 1),
            'details': self.details
        }
    
    def __repr__(self) -> str:
        return f"Signal({self.type}, {self.direction}, {self.timeframe}, strength={self.strength:.0f})"


@dataclass
class Bias:
    """Final trading bias with confidence"""
    direction: BiasDirection
    confidence: float  # 0-100
    confidence_level: ConfidenceLevel
    bullish_score: float
    bearish_score: float
    signals: List[Signal] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def neutral(cls, reason: str = "No signals") -> 'Bias':
        """Create a neutral bias"""
        return cls(
            direction=BiasDirection.NEUTRAL,
            confidence=0.0,
            confidence_level=ConfidenceLevel.NEUTRAL,
            bullish_score=0.0,
            bearish_score=0.0,
            signals=[],
            metadata={'reason': reason}
        )
    
    def to_dict(self) -> dict:
        return {
            'direction': self.direction.value,
            'confidence': round(self.confidence, 1),
            'confidence_level': self.confidence_level.value,
            'bullish_score': round(self.bullish_score, 1),
            'bearish_score': round(self.bearish_score, 1),
            'signal_count': len(self.signals),
            'signals_by_type': self._count_signals_by_type(),
            'metadata': self.metadata
        }
    
    def _count_signals_by_type(self) -> dict:
        """Count signals by type"""
        counts = {}
        for signal in self.signals:
            counts[signal.type] = counts.get(signal.type, 0) + 1
        return counts
    
    def __repr__(self) -> str:
        return (f"Bias({self.direction.value}, "
                f"confidence={self.confidence:.1f}%, "
                f"level={self.confidence_level.value})")


# ============================================================================
# BIAS CALCULATOR
# ============================================================================

class BiasCalculator:
    """
    Calculates final trading bias from multiple SMC signals
    
    Uses weighted scoring system where different signal types
    have different importance. Determines bias direction and
    confidence level based on aggregate scores.
    
    Signal Weights:
    - market_structure: 35% (most important)
    - order_block: 30%
    - fvg: 20%
    - momentum: 10%
    - volume: 5%
    
    Confidence Thresholds:
    - HIGH: ≥75%
    - MEDIUM: 55-74%
    - LOW: 40-54%
    - NEUTRAL: <40%
    """
    
    # Default signal weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'market_structure': 0.35,
        'order_block': 0.30,
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
    
    def __init__(self, signal_weights: Optional[Dict[str, float]] = None):
        """
        Initialize Bias Calculator
        
        Args:
            signal_weights: Custom signal weights (optional)
        """
        self.signal_weights = signal_weights or self.DEFAULT_WEIGHTS
        self.logger = logging.getLogger(f"{__name__}.BiasCalculator")
        
        # Validate weights
        total = sum(self.signal_weights.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            self.logger.warning(f"Signal weights sum to {total}, should be 1.0")
    
    def calculate(self, signals: List[Signal]) -> Bias:
        """
        Calculate final bias from signals
        
        Args:
            signals: List of SMC signals
        
        Returns:
            Bias object with direction and confidence
        """
        if not signals:
            self.logger.warning("No signals provided")
            return Bias.neutral("No signals provided")
        
        try:
            self.logger.info(f"Calculating bias from {len(signals)} signals")
            
            # Group signals by type
            signals_by_type = self._group_signals_by_type(signals)
            self.logger.debug(f"Signal types: {list(signals_by_type.keys())}")
            
            # Calculate weighted scores
            bullish_score, bearish_score = self._calculate_scores(signals_by_type)
            
            self.logger.debug(f"Scores: Bullish={bullish_score:.1f}%, Bearish={bearish_score:.1f}%")
            
            # Determine bias direction
            direction, confidence = self._determine_bias(bullish_score, bearish_score)
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(confidence)
            
            # Create bias object
            bias = Bias(
                direction=direction,
                confidence=confidence,
                confidence_level=confidence_level,
                bullish_score=bullish_score,
                bearish_score=bearish_score,
                signals=signals,
                metadata={
                    'signal_types': list(signals_by_type.keys()),
                    'total_signals': len(signals)
                }
            )
            
            self.logger.info(
                f"Bias: {direction.value} "
                f"(confidence={confidence:.1f}%, level={confidence_level.value})"
            )
            
            return bias
            
        except Exception as e:
            self.logger.exception(f"Error calculating bias: {e}")
            return Bias.neutral(f"Calculation error: {e}")
    
    def _group_signals_by_type(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        """Group signals by type"""
        grouped = {}
        for signal in signals:
            if signal.type not in grouped:
                grouped[signal.type] = []
            grouped[signal.type].append(signal)
        return grouped
    
    def _calculate_scores(self, signals_by_type: Dict[str, List[Signal]]) -> tuple[float, float]:
        """Calculate weighted bullish and bearish scores"""
        bullish_score = 0.0
        bearish_score = 0.0
        max_possible = 0.0
        
        for signal_type, signal_list in signals_by_type.items():
            weight = self.signal_weights.get(signal_type, 0)
            if weight == 0:
                self.logger.debug(f"Skipping {signal_type} (no weight assigned)")
                continue
            
            max_possible += weight * 100
            
            # Calculate average strength for this signal type
            total_strength = sum(s.strength for s in signal_list)
            avg_strength = total_strength / len(signal_list)
            
            # Count bullish and bearish signals
            bullish_signals = [s for s in signal_list if s.direction == 'BULLISH']
            bearish_signals = [s for s in signal_list if s.direction == 'BEARISH']
            
            # Add to scores based on direction
            if bullish_signals:
                bullish_contribution = (len(bullish_signals) / len(signal_list)) * avg_strength
                bullish_score += weight * bullish_contribution
                
            if bearish_signals:
                bearish_contribution = (len(bearish_signals) / len(signal_list)) * avg_strength
                bearish_score += weight * bearish_contribution
        
        # Normalize to percentage
        if max_possible > 0:
            bullish_pct = (bullish_score / max_possible) * 100
            bearish_pct = (bearish_score / max_possible) * 100
        else:
            bullish_pct = bearish_pct = 0.0
        
        return bullish_pct, bearish_pct
    
    def _determine_bias(self, bullish_score: float, bearish_score: float) -> tuple[BiasDirection, float]:
        """Determine bias direction and confidence"""
        # Check which score is higher
        if bullish_score > bearish_score:
            if bullish_score >= self.CONFIDENCE_THRESHOLDS['LOW']:
                return BiasDirection.BULLISH, bullish_score
            else:
                return BiasDirection.NEUTRAL, bullish_score
        
        elif bearish_score > bullish_score:
            if bearish_score >= self.CONFIDENCE_THRESHOLDS['LOW']:
                return BiasDirection.BEARISH, bearish_score
            else:
                return BiasDirection.NEUTRAL, bearish_score
        
        else:
            # Scores are equal or both zero
            return BiasDirection.NEUTRAL, max(bullish_score, bearish_score)
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from confidence percentage"""
        if confidence >= self.CONFIDENCE_THRESHOLDS['HIGH']:
            return ConfidenceLevel.HIGH
        elif confidence >= self.CONFIDENCE_THRESHOLDS['MEDIUM']:
            return ConfidenceLevel.MEDIUM
        elif confidence >= self.CONFIDENCE_THRESHOLDS['LOW']:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NEUTRAL


# ============================================================================
# MULTI-TIMEFRAME CONFLUENCE ANALYZER
# ============================================================================

class ConfluenceAnalyzer:
    """
    Analyzes confluence across multiple timeframes
    
    Checks alignment between higher, middle, and lower timeframes
    to determine overall strength of bias.
    """
    
    TIMEFRAME_GROUPS = {
        'HTF': ['W1', 'D1'],      # Higher Timeframe
        'MTF': ['H4', 'H1'],      # Middle Timeframe
        'LTF': ['M15', 'M5']      # Lower Timeframe
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ConfluenceAnalyzer")
    
    def analyze_confluence(self, signals_by_timeframe: Dict[str, List[Signal]]) -> dict:
        """
        Analyze multi-timeframe confluence
        
        Args:
            signals_by_timeframe: Signals grouped by timeframe
        
        Returns:
            Confluence analysis dictionary
        """
        try:
            # Group by timeframe category
            htf_signals = self._get_signals_for_group(signals_by_timeframe, 'HTF')
            mtf_signals = self._get_signals_for_group(signals_by_timeframe, 'MTF')
            ltf_signals = self._get_signals_for_group(signals_by_timeframe, 'LTF')
            
            # Determine bias for each group
            calculator = BiasCalculator()
            
            htf_bias = calculator.calculate(htf_signals) if htf_signals else Bias.neutral()
            mtf_bias = calculator.calculate(mtf_signals) if mtf_signals else Bias.neutral()
            ltf_bias = calculator.calculate(ltf_signals) if ltf_signals else Bias.neutral()
            
            # Calculate confluence score
            confluence_score = self._calculate_confluence_score(htf_bias, mtf_bias, ltf_bias)
            
            return {
                'htf_bias': htf_bias.direction.value,
                'mtf_bias': mtf_bias.direction.value,
                'ltf_bias': ltf_bias.direction.value,
                'confluence_score': confluence_score,
                'alignment': self._determine_alignment(htf_bias, mtf_bias, ltf_bias)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing confluence: {e}")
            return {
                'htf_bias': 'NEUTRAL',
                'mtf_bias': 'NEUTRAL',
                'ltf_bias': 'NEUTRAL',
                'confluence_score': 0,
                'alignment': 'NONE'
            }
    
    def _get_signals_for_group(self, signals_by_tf: Dict[str, List[Signal]], group: str) -> List[Signal]:
        """Get all signals for a timeframe group"""
        timeframes = self.TIMEFRAME_GROUPS.get(group, [])
        signals = []
        for tf in timeframes:
            signals.extend(signals_by_tf.get(tf, []))
        return signals
    
    def _calculate_confluence_score(self, htf: Bias, mtf: Bias, ltf: Bias) -> float:
        """Calculate confluence score (0-100)"""
        # Perfect alignment: all same direction
        if htf.direction == mtf.direction == ltf.direction and htf.direction != BiasDirection.NEUTRAL:
            return 100.0
        
        # Strong alignment: HTF and MTF agree
        if htf.direction == mtf.direction and htf.direction != BiasDirection.NEUTRAL:
            return 80.0
        
        # Moderate alignment: HTF has clear direction
        if htf.direction != BiasDirection.NEUTRAL:
            return 60.0
        
        # Weak/no alignment
        return 40.0
    
    def _determine_alignment(self, htf: Bias, mtf: Bias, ltf: Bias) -> str:
        """Determine alignment quality"""
        if htf.direction == mtf.direction == ltf.direction and htf.direction != BiasDirection.NEUTRAL:
            return 'PERFECT'
        elif htf.direction == mtf.direction and htf.direction != BiasDirection.NEUTRAL:
            return 'STRONG'
        elif htf.direction != BiasDirection.NEUTRAL:
            return 'MODERATE'
        else:
            return 'WEAK'


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Bias Calculator - Module Test")
    print("="*70)
    
    # Create test signals
    signals = [
        Signal('market_structure', 'BULLISH', 75, 'D1', 75),
        Signal('market_structure', 'BULLISH', 68, 'H4', 68),
        Signal('order_block', 'BULLISH', 82, 'H4', 82),
        Signal('order_block', 'BEARISH', 55, 'H1', 55),
        Signal('fvg', 'BULLISH', 70, 'H4', 70),
    ]
    
    print(f"\nTest Signals ({len(signals)}):")
    for s in signals:
        print(f"  - {s}")
    
    # Calculate bias
    print("\nCalculating bias...")
    calculator = BiasCalculator()
    bias = calculator.calculate(signals)
    
    print("\nResult:")
    print(f"  Direction: {bias.direction.value}")
    print(f"  Confidence: {bias.confidence:.1f}%")
    print(f"  Level: {bias.confidence_level.value}")
    print(f"  Bullish Score: {bias.bullish_score:.1f}%")
    print(f"  Bearish Score: {bias.bearish_score:.1f}%")
    
    print("\n" + "="*70)
    print("✅ Bias calculator tested successfully!")
