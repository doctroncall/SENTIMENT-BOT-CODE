"""
SMC Engine - Main Orchestrator
===============================

Production-grade SMC analysis orchestrator that:
1. Coordinates all SMC detectors
2. Aggregates signals
3. Calculates final bias
4. Generates reports
5. Handles errors gracefully

Author: Trading Bot Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .smc_components import (
    OrderBlockDetector,
    MarketStructureAnalyzer,
    FairValueGapDetector,
    OrderBlock,
    FairValueGap,
    MarketStructure
)

from .bias_calculator import (
    BiasCalculator,
    ConfluenceAnalyzer,
    Bias,
    Signal,
    BiasDirection,
    ConfidenceLevel
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# SMC ENGINE
# ============================================================================

class SMCEngine:
    """
    Main SMC Analysis Engine
    
    Orchestrates the entire SMC analysis process:
    - Validates input data
    - Runs SMC detectors on each timeframe
    - Aggregates signals
    - Calculates final bias
    - Generates comprehensive report
    
    Features:
    - Robust error handling (never crashes)
    - Graceful degradation (continues if one TF fails)
    - Comprehensive logging
    - Performance monitoring
    - Data validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize SMC Engine
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        
        # Initialize detectors
        self.ob_detector = OrderBlockDetector(
            min_strength=self.config.get('ob_min_strength', 60),
            body_threshold=self.config.get('ob_body_threshold', 0.5)
        )
        
        self.structure_analyzer = MarketStructureAnalyzer(
            swing_lookback=self.config.get('structure_lookback', 5)
        )
        
        self.fvg_detector = FairValueGapDetector(
            min_gap_atr_multiplier=self.config.get('fvg_min_gap', 0.5),
            atr_period=self.config.get('fvg_atr_period', 14)
        )
        
        # Initialize calculators
        self.bias_calculator = BiasCalculator(
            signal_weights=self.config.get('signal_weights')
        )
        
        self.confluence_analyzer = ConfluenceAnalyzer()
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.SMCEngine")
        
        self.logger.info("SMC Engine initialized")
    
    def analyze(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Bias:
        """
        Analyze symbol using SMC concepts
        
        Args:
            symbol: Trading symbol (e.g., 'GBPUSD')
            data: Dictionary of {timeframe: DataFrame}
        
        Returns:
            Bias object with final trading direction and confidence
        """
        self.logger.info("="*70)
        self.logger.info(f"SMC Analysis Starting: {symbol}")
        self.logger.info("="*70)
        
        try:
            # Step 1: Validate input data
            if not self._validate_data(data):
                self.logger.error("❌ Data validation failed")
                return Bias.neutral("Data validation failed")
            
            self.logger.info(f"✅ Data validated: {list(data.keys())}")
            
            # Step 2: Run SMC analysis on each timeframe
            all_signals = []
            signals_by_timeframe = {}
            
            for timeframe in sorted(data.keys()):
                self.logger.info(f"\n📊 Analyzing {timeframe}...")
                self.logger.info("-"*70)
                
                try:
                    signals = self._analyze_timeframe(data[timeframe], timeframe)
                    all_signals.extend(signals)
                    signals_by_timeframe[timeframe] = signals
                    
                    self.logger.info(f"✅ {timeframe}: {len(signals)} signals generated")
                    
                except Exception as e:
                    self.logger.error(f"❌ {timeframe} analysis failed: {e}")
                    # Continue with other timeframes
                    continue
            
            if not all_signals:
                self.logger.error("❌ No signals generated from any timeframe")
                return Bias.neutral("No signals generated")
            
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"📊 Total signals collected: {len(all_signals)}")
            self.logger.info(f"{'='*70}")
            
            # Step 3: Analyze multi-timeframe confluence
            confluence = self.confluence_analyzer.analyze_confluence(signals_by_timeframe)
            self.logger.info(f"\n🔀 Confluence Analysis:")
            self.logger.info(f"   HTF: {confluence['htf_bias']}")
            self.logger.info(f"   MTF: {confluence['mtf_bias']}")
            self.logger.info(f"   LTF: {confluence['ltf_bias']}")
            self.logger.info(f"   Alignment: {confluence['alignment']}")
            self.logger.info(f"   Score: {confluence['confluence_score']:.0f}/100")
            
            # Step 4: Calculate final bias
            self.logger.info(f"\n{'='*70}")
            self.logger.info("Calculating final bias...")
            self.logger.info(f"{'='*70}")
            
            bias = self.bias_calculator.calculate(all_signals)
            
            # Add confluence data to bias metadata
            bias.metadata['confluence'] = confluence
            bias.metadata['symbol'] = symbol
            bias.metadata['timestamp'] = datetime.now().isoformat()
            bias.metadata['timeframes_analyzed'] = list(data.keys())
            
            # Step 5: Validate result
            if not self._validate_bias(bias, all_signals):
                self.logger.warning("⚠️ Bias validation warning - review recommended")
            
            # Final summary
            self.logger.info(f"\n{'='*70}")
            self.logger.info("✅ SMC ANALYSIS COMPLETE")
            self.logger.info(f"{'='*70}")
            self.logger.info(f"Symbol: {symbol}")
            self.logger.info(f"Bias: {bias.direction.value}")
            self.logger.info(f"Confidence: {bias.confidence:.1f}%")
            self.logger.info(f"Level: {bias.confidence_level.value}")
            self.logger.info(f"Bullish Score: {bias.bullish_score:.1f}%")
            self.logger.info(f"Bearish Score: {bias.bearish_score:.1f}%")
            self.logger.info(f"Signals: {len(all_signals)} total")
            self.logger.info(f"{'='*70}\n")
            
            return bias
            
        except Exception as e:
            self.logger.exception(f"❌ Critical error in SMC analysis: {e}")
            return Bias.neutral(f"Critical error: {str(e)}")
    
    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate input data quality"""
        if not data:
            self.logger.error("No data provided")
            return False
        
        for tf, df in data.items():
            if df is None or df.empty:
                self.logger.error(f"Empty DataFrame for {tf}")
                return False
            
            # Check required columns
            required = ['open', 'high', 'low', 'close']
            missing = [col for col in required if col not in df.columns]
            if missing:
                self.logger.error(f"{tf} missing columns: {missing}")
                return False
            
            # Check minimum bars
            if len(df) < 30:
                self.logger.warning(f"{tf} has only {len(df)} bars (recommend 30+)")
        
        return True
    
    def _analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> List[Signal]:
        """
        Analyze single timeframe and generate signals
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe string
        
        Returns:
            List of signals
        """
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
                    details=ob.to_dict()
                )
                signals.append(signal)
            
            bullish_count = sum(1 for ob in obs if ob.type == 'bullish')
            bearish_count = sum(1 for ob in obs if ob.type == 'bearish')
            self.logger.info(f"   Order Blocks: {len(obs)} ({bullish_count} bullish, {bearish_count} bearish)")
            
        except Exception as e:
            self.logger.error(f"   Order Block detection failed: {e}")
        
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
                    details=structure.to_dict()
                )
                signals.append(signal)
            
            self.logger.info(
                f"   Market Structure: {structure.trend} "
                f"(strength={structure.structure_strength:.0f}, "
                f"{len(structure.swing_highs)}H/{len(structure.swing_lows)}L)"
            )
            
        except Exception as e:
            self.logger.error(f"   Market Structure analysis failed: {e}")
        
        # 3. Fair Value Gaps
        try:
            fvgs = self.fvg_detector.detect(df, timeframe)
            for fvg in fvgs:
                signal = Signal(
                    type='fvg',
                    direction='BULLISH' if fvg.type == 'bullish' else 'BEARISH',
                    strength=70.0,  # FVGs have fixed strength
                    timeframe=timeframe,
                    confidence=70.0,
                    details=fvg.to_dict()
                )
                signals.append(signal)
            
            bullish_fvg = sum(1 for fvg in fvgs if fvg.type == 'bullish')
            bearish_fvg = sum(1 for fvg in fvgs if fvg.type == 'bearish')
            self.logger.info(f"   Fair Value Gaps: {len(fvgs)} ({bullish_fvg} bullish, {bearish_fvg} bearish)")
            
        except Exception as e:
            self.logger.error(f"   FVG detection failed: {e}")
        
        return signals
    
    def _validate_bias(self, bias: Bias, signals: List[Signal]) -> bool:
        """Validate bias result makes sense"""
        # High confidence should have multiple confirming signals
        if bias.confidence_level == ConfidenceLevel.HIGH:
            confirming = sum(
                1 for s in signals 
                if s.direction == bias.direction.value
            )
            if confirming < 2:
                self.logger.warning(
                    f"High confidence ({bias.confidence:.1f}%) "
                    f"with only {confirming} confirming signal(s)"
                )
                return False
        
        # Bias should ideally have structure support
        if bias.direction != BiasDirection.NEUTRAL:
            has_structure = any(
                s.type == 'market_structure' and 
                s.direction == bias.direction.value
                for s in signals
            )
            if not has_structure:
                self.logger.warning(
                    f"{bias.direction.value} bias without market structure support"
                )
                # Don't fail, just warn
        
        return True
    
    def generate_report(self, symbol: str, bias: Bias) -> str:
        """
        Generate human-readable analysis report
        
        Args:
            symbol: Trading symbol
            bias: Bias result
        
        Returns:
            Formatted markdown report
        """
        report = f"""
# SMC Analysis Report: {symbol}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

---

## 📊 Final Bias

- **Direction:** {bias.direction.value}
- **Confidence:** {bias.confidence:.1f}%
- **Confidence Level:** {bias.confidence_level.value}

---

## 📈 Score Breakdown

- **Bullish Score:** {bias.bullish_score:.1f}%
- **Bearish Score:** {bias.bearish_score:.1f}%

---

## 🎯 Signals Summary ({len(bias.signals)} total)

"""
        
        # Group signals by type
        signals_by_type = {}
        for signal in bias.signals:
            if signal.type not in signals_by_type:
                signals_by_type[signal.type] = []
            signals_by_type[signal.type].append(signal)
        
        for signal_type, signal_list in signals_by_type.items():
            report += f"\n### {signal_type.replace('_', ' ').title()}\n"
            
            bullish = [s for s in signal_list if s.direction == 'BULLISH']
            bearish = [s for s in signal_list if s.direction == 'BEARISH']
            
            if bullish:
                report += f"- Bullish: {len(bullish)} signal(s)\n"
                for s in bullish:
                    report += f"  - {s.timeframe}: strength={s.strength:.0f}\n"
            
            if bearish:
                report += f"- Bearish: {len(bearish)} signal(s)\n"
                for s in bearish:
                    report += f"  - {s.timeframe}: strength={s.strength:.0f}\n"
        
        # Add confluence data
        if 'confluence' in bias.metadata:
            confluence = bias.metadata['confluence']
            report += f"\n---\n\n## 🔀 Multi-Timeframe Confluence\n\n"
            report += f"- **HTF Bias:** {confluence['htf_bias']}\n"
            report += f"- **MTF Bias:** {confluence['mtf_bias']}\n"
            report += f"- **LTF Bias:** {confluence['ltf_bias']}\n"
            report += f"- **Alignment:** {confluence['alignment']}\n"
            report += f"- **Confluence Score:** {confluence['confluence_score']:.0f}/100\n"
        
        report += f"\n---\n\n## 💡 Recommendation\n\n"
        
        if bias.confidence_level == ConfidenceLevel.HIGH:
            report += f"**Strong {bias.direction.value} bias** with high confidence. "
            report += f"Consider {bias.direction.value.lower()} positions.\n"
        elif bias.confidence_level == ConfidenceLevel.MEDIUM:
            report += f"**Moderate {bias.direction.value} bias** with medium confidence. "
            report += f"Wait for confirmation before entering {bias.direction.value.lower()} positions.\n"
        elif bias.confidence_level == ConfidenceLevel.LOW:
            report += f"**Weak {bias.direction.value} bias** with low confidence. "
            report += "Wait for clearer signals.\n"
        else:
            report += "**Neutral bias** - No clear direction. Stay on sidelines.\n"
        
        report += "\n---\n\n*Generated by SMC Analysis Engine v1.0*\n"
        
        return report


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import numpy as np
    
    print("\n" + "="*70)
    print("SMC Engine - Integration Test")
    print("="*70 + "\n")
    
    # Create sample multi-timeframe data
    dates_d1 = pd.date_range(start='2025-01-01', periods=90, freq='D', tz='UTC')
    dates_h4 = pd.date_range(start='2025-01-01', periods=180, freq='4H', tz='UTC')
    dates_h1 = pd.date_range(start='2025-01-01', periods=360, freq='H', tz='UTC')
    
    np.random.seed(42)
    
    def create_trending_data(dates, trend_strength=0.0001):
        """Create sample OHLC data with trend"""
        base = 1.2700
        trend = np.linspace(0, trend_strength * len(dates), len(dates))
        noise = np.random.normal(0, 0.0005, len(dates))
        prices = base + trend + noise
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.0001, len(prices))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0003, len(prices)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0003, len(prices)))),
            'close': prices,
        }, index=dates)
        
        # Ensure OHLC validity
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    # Create data with bullish bias
    data = {
        'D1': create_trending_data(dates_d1, 0.0001),  # Strong uptrend
        'H4': create_trending_data(dates_h4, 0.00008),  # Medium uptrend
        'H1': create_trending_data(dates_h1, 0.00005),  # Weak uptrend
    }
    
    print("Sample data created:")
    for tf, df in data.items():
        print(f"  {tf}: {len(df)} bars")
    
    # Run SMC analysis
    print("\nRunning SMC analysis...")
    print("="*70)
    
    engine = SMCEngine()
    bias = engine.analyze('GBPUSD', data)
    
    # Display results
    print("\n" + "="*70)
    print("FINAL RESULT")
    print("="*70)
    print(f"Bias: {bias.direction.value}")
    print(f"Confidence: {bias.confidence:.1f}%")
    print(f"Level: {bias.confidence_level.value}")
    print(f"Bullish Score: {bias.bullish_score:.1f}%")
    print(f"Bearish Score: {bias.bearish_score:.1f}%")
    print(f"Total Signals: {len(bias.signals)}")
    
    # Generate report
    print("\n" + "="*70)
    print("GENERATING REPORT")
    print("="*70)
    report = engine.generate_report('GBPUSD', bias)
    print(report)
    
    print("\n✅ SMC Engine test complete!")
