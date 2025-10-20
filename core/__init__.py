"""
Core SMC Analysis Components
=============================

Production-grade Smart Money Concepts analysis engine.

Components:
- smc_components.py: SMC detectors (Order Blocks, Structure, FVG, Liquidity)
- bias_calculator.py: Weighted scoring and bias determination
- smc_engine.py: Main orchestrator
"""

__version__ = "1.0.0"
__author__ = "Trading Bot Team"

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
    Bias,
    BiasDirection,
    ConfidenceLevel,
    Signal
)

from .smc_engine import SMCEngine

__all__ = [
    # Detectors
    'OrderBlockDetector',
    'MarketStructureAnalyzer',
    'FairValueGapDetector',
    
    # Data Models
    'OrderBlock',
    'FairValueGap',
    'MarketStructure',
    'Bias',
    'BiasDirection',
    'ConfidenceLevel',
    'Signal',
    
    # Main Engine
    'SMCEngine'
]
