"""
Dashboard - SMC Version
=======================

Production-grade trading dashboard using Smart Money Concepts analysis.

This version replaces the old sentiment engine with the new SMC system
while maintaining all existing functionality.

Author: Trading Bot Team
Version: 2.0.0 (SMC)
"""

import os
import sys
import time
import yaml
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

# Core data layer (keep our improved version)
from data_manager import DataManager, normalize_symbol

# New SMC system
from core import SMCEngine, Bias, BiasDirection, ConfidenceLevel

# Keep existing utilities
try:
    from status_monitor import (
        get_monitor, log_info, log_success, log_error, 
        log_warning, log_data_fetch, log_analysis
    )
    STATUS_MONITOR_AVAILABLE = True
except ImportError:
    STATUS_MONITOR_AVAILABLE = False
    # Fallback logging
    def log_info(msg, **kwargs): print(f"ℹ️ {msg}")
    def log_success(msg, **kwargs): print(f"✅ {msg}")
    def log_error(msg, **kwargs): print(f"❌ {msg}")
    def log_warning(msg, **kwargs): print(f"⚠️ {msg}")
    def log_data_fetch(msg, **kwargs): print(f"📡 {msg}")
    def log_analysis(msg, **kwargs): print(f"📊 {msg}")


class Dashboard:
    """
    Production-Grade Trading Dashboard with SMC Analysis
    
    Features:
    - Smart Money Concepts analysis
    - Multi-timeframe confluence
    - Weighted bias calculation
    - Robust error handling
    - Excel logging
    - Comprehensive reporting
    """
    
    def __init__(self, symbols: Optional[List[str]] = None, config_path: str = "config/smc_config.yaml"):
        """
        Initialize dashboard
        
        Args:
            symbols: List of trading symbols
            config_path: Path to SMC configuration file
        """
        # Normalize symbols
        self.symbols = [normalize_symbol(s) for s in (symbols or ["GBPUSD", "XAUUSD"])]
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        try:
            log_info("Initializing Dashboard (SMC version)...")
            
            # Data manager (our improved version)
            self.data_manager = DataManager()
            
            # SMC Engine (new!)
            self.smc_engine = SMCEngine(config=self.config.get('smc_analysis', {}).get('components', {}))
            
            # Excel logging
            self.excel_file = self.config.get('excel', {}).get('file', 'smc_analysis_log.xlsx')
            
            # Timeframes to analyze
            self.timeframes = self.config.get('smc_analysis', {}).get('timeframes', {}).get('use', ['D1', 'H4', 'H1'])
            
            print(f"\n{'='*70}")
            print("✅ Dashboard Initialized (SMC System)")
            print(f"{'='*70}")
            print(f"Symbols: {', '.join(self.symbols)}")
            print(f"Timeframes: {', '.join(self.timeframes)}")
            print(f"Excel Log: {self.excel_file}")
            print(f"SMC Engine: Ready")
            print(f"{'='*70}\n")
            
            log_success(f"Dashboard initialized for {len(self.symbols)} symbols")
            
        except Exception as e:
            print(f"❌ Error initializing dashboard: {e}")
            log_error(f"Dashboard initialization failed: {e}")
            raise
    
    def _load_config(self, config_path: str) -> dict:
        """Load YAML configuration"""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                log_info(f"Configuration loaded from {config_path}")
                return config
            except Exception as e:
                log_warning(f"Failed to load config from {config_path}: {e}")
        
        # Return default config
        return {
            'smc_analysis': {
                'timeframes': {'use': ['D1', 'H4', 'H1']},
                'components': {}
            },
            'excel': {'file': 'smc_analysis_log.xlsx'}
        }
    
    # ========================================================================
    # MAIN ANALYSIS METHODS
    # ========================================================================
    
    def run_full_cycle(self) -> List[Dict]:
        """
        Run complete SMC analysis for all symbols
        
        Returns:
            List of analysis results
        """
        print("\n" + "="*70)
        print("🚀 Starting Full SMC Analysis Cycle")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("="*70)
        
        log_analysis(f"Starting full cycle for {len(self.symbols)} symbols")
        
        # Ensure MT5 connection
        if not self._ensure_mt5_connection():
            log_error("MT5 connection failed - aborting cycle")
            return []
        
        results = []
        
        for symbol in self.symbols:
            print(f"\n{'='*70}")
            print(f"Analyzing: {symbol}")
            print(f"{'='*70}")
            
            try:
                result = self.analyze_symbol(symbol)
                results.append(result)
                
                if result['success']:
                    print(f"✅ {symbol}: {result['bias']} ({result['confidence']:.1f}%)")
                else:
                    print(f"❌ {symbol}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ {symbol} analysis failed: {e}")
                log_error(f"{symbol} analysis error", str(e))
                results.append({
                    'success': False,
                    'symbol': symbol,
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'='*70}")
        print(f"✅ Cycle Complete: {successful}/{len(self.symbols)} successful")
        print(f"{'='*70}\n")
        
        log_analysis(f"Cycle complete: {successful}/{len(self.symbols)} successful")
        
        return results
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Analyze single symbol using SMC
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Analysis result dictionary
        """
        symbol = normalize_symbol(symbol)
        
        log_analysis(f"Starting SMC analysis for {symbol}")
        
        try:
            # Step 1: Fetch multi-timeframe data
            print(f"\n📊 Fetching data for {symbol}...")
            log_data_fetch(f"Fetching {symbol} data across {len(self.timeframes)} timeframes")
            
            data = self.data_manager.get_symbol_data(
                symbol,
                timeframes=self.timeframes,
                lookback_days=90,
                use_yahoo_fallback=False
            )
            
            if not data:
                error_msg = f"No data available for {symbol}"
                log_error(error_msg)
                return {
                    'success': False,
                    'symbol': symbol,
                    'error': error_msg
                }
            
            print(f"✅ Data collected: {list(data.keys())}")
            
            # Step 2: Run SMC analysis
            print(f"\n🔍 Running SMC analysis...")
            bias = self.smc_engine.analyze(symbol, data)
            
            # Step 3: Generate report
            report = self.smc_engine.generate_report(symbol, bias)
            
            # Step 4: Log to Excel
            self._log_to_excel(symbol, bias, report)
            
            # Step 5: Create result
            result = {
                'success': True,
                'symbol': symbol,
                'bias': bias.direction.value,
                'confidence': bias.confidence,
                'confidence_level': bias.confidence_level.value,
                'bullish_score': bias.bullish_score,
                'bearish_score': bias.bearish_score,
                'signal_count': len(bias.signals),
                'timeframes': list(data.keys()),
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
            
            log_success(
                f"{symbol} analysis complete",
                bias=bias.direction.value,
                confidence=f"{bias.confidence:.1f}%"
            )
            
            return result
            
        except Exception as e:
            log_error(f"{symbol} analysis failed", str(e))
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def run_manual_analysis(self, symbol: str) -> Dict:
        """
        Run manual analysis for specific symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Analysis result
        """
        print(f"\n{'='*70}")
        print(f"📊 Manual Analysis: {symbol}")
        print(f"{'='*70}")
        
        result = self.analyze_symbol(symbol)
        
        if result['success']:
            print(f"\n{result['report']}")
        
        return result
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _ensure_mt5_connection(self) -> bool:
        """Ensure MT5 is connected"""
        if not self.data_manager.use_mt5:
            print("ℹ️ MT5 disabled")
            return True  # Not using MT5, so "success"
        
        if self.data_manager.is_connected():
            print("✅ MT5 already connected")
            return True
        
        print("\n🔌 Connecting to MT5...")
        log_info("Connecting to MT5...")
        
        connected = self.data_manager.connect()
        
        if connected:
            print("✅ MT5 connected successfully")
            log_success("MT5 connected")
            return True
        else:
            print("❌ MT5 connection failed")
            log_error("MT5 connection failed")
            return False
    
    def _log_to_excel(self, symbol: str, bias: Bias, report: str):
        """
        Log analysis to Excel
        
        Args:
            symbol: Trading symbol
            bias: Bias result
            report: Analysis report
        """
        try:
            # Prepare row data
            row_data = {
                'Date': datetime.now(),
                'Symbol': symbol,
                'Bias': bias.direction.value,
                'Confidence': bias.confidence,
                'Confidence Level': bias.confidence_level.value,
                'Bullish Score': bias.bullish_score,
                'Bearish Score': bias.bearish_score,
                'Signal Count': len(bias.signals),
                'Timeframes': ', '.join(bias.metadata.get('timeframes_analyzed', [])),
                'Report': report[:500]  # Limit report length for Excel
            }
            
            # Add signal breakdown
            if bias.signals:
                signal_types = {}
                for signal in bias.signals:
                    signal_types[signal.type] = signal_types.get(signal.type, 0) + 1
                
                row_data['OB Signals'] = signal_types.get('order_block', 0)
                row_data['Structure Signals'] = signal_types.get('market_structure', 0)
                row_data['FVG Signals'] = signal_types.get('fvg', 0)
            
            # Read existing data or create new
            if os.path.exists(self.excel_file):
                df = pd.read_excel(self.excel_file)
                df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
            else:
                df = pd.DataFrame([row_data])
            
            # Save
            df.to_excel(self.excel_file, index=False)
            log_success(f"Logged to {self.excel_file}")
            
        except Exception as e:
            log_error(f"Failed to log to Excel: {e}")
    
    def health_check(self) -> bool:
        """
        Run system health check
        
        Returns:
            True if all systems OK
        """
        print("\n" + "="*70)
        print("🏥 Running System Health Check")
        print("="*70)
        
        checks = []
        
        # Check 1: Data Manager
        print("\n1️⃣ Data Manager...")
        if self.data_manager:
            print("   ✅ Data Manager initialized")
            checks.append(True)
        else:
            print("   ❌ Data Manager missing")
            checks.append(False)
        
        # Check 2: SMC Engine
        print("2️⃣ SMC Engine...")
        if self.smc_engine:
            print("   ✅ SMC Engine initialized")
            checks.append(True)
        else:
            print("   ❌ SMC Engine missing")
            checks.append(False)
        
        # Check 3: MT5 Connection
        print("3️⃣ MT5 Connection...")
        if self.data_manager.use_mt5:
            if self.data_manager.is_connected():
                print("   ✅ MT5 connected")
                checks.append(True)
            else:
                print("   ⚠️  MT5 not connected (will connect when needed)")
                checks.append(True)  # Not a failure
        else:
            print("   ℹ️  MT5 disabled")
            checks.append(True)
        
        # Check 4: Excel file
        print("4️⃣ Excel Logging...")
        try:
            # Check if we can write to Excel file
            test_df = pd.DataFrame([{'test': 'test'}])
            test_file = 'test_excel.xlsx'
            test_df.to_excel(test_file, index=False)
            os.remove(test_file)
            print("   ✅ Excel logging available")
            checks.append(True)
        except Exception as e:
            print(f"   ❌ Excel logging issue: {e}")
            checks.append(False)
        
        # Check 5: Configuration
        print("5️⃣ Configuration...")
        if self.config:
            print("   ✅ Configuration loaded")
            checks.append(True)
        else:
            print("   ⚠️  Using default configuration")
            checks.append(True)
        
        # Summary
        passed = sum(checks)
        total = len(checks)
        
        print(f"\n{'='*70}")
        if passed == total:
            print(f"✅ All Checks Passed ({passed}/{total})")
            print(f"{'='*70}\n")
            return True
        else:
            print(f"⚠️  Some Checks Failed ({passed}/{total})")
            print(f"{'='*70}\n")
            return False
    
    def get_latest_analysis(self, symbol: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        """
        Get latest analysis results from Excel
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Number of results to return
        
        Returns:
            DataFrame with latest results
        """
        if not os.path.exists(self.excel_file):
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(self.excel_file)
            
            if symbol:
                df = df[df['Symbol'] == normalize_symbol(symbol)]
            
            return df.tail(limit).sort_values('Date', ascending=False)
            
        except Exception as e:
            log_error(f"Error reading Excel: {e}")
            return pd.DataFrame()


# ============================================================================
# MAIN - Testing
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Dashboard (SMC Version) - Test Run")
    print("="*70 + "\n")
    
    # Create dashboard
    dashboard = Dashboard(symbols=["GBPUSD", "XAUUSD"])
    
    # Health check
    dashboard.health_check()
    
    # Test manual analysis (if MT5 is available)
    print("\nWould you like to run a test analysis? (requires MT5)")
    print("Note: This is a test. Remove this section for production use.")
    
    # For automated testing, you can uncomment:
    # result = dashboard.run_manual_analysis("GBPUSD")
    # if result['success']:
    #     print(f"\n✅ Test successful!")
    #     print(f"Bias: {result['bias']}")
    #     print(f"Confidence: {result['confidence']:.1f}%")
