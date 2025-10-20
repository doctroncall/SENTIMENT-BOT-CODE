#!/usr/bin/env python3
"""
Production-Grade MT5 Data Collection & Analysis Bot
====================================================

A professional, production-ready trading bot that:
- Collects data from MetaTrader 5
- Analyzes using Smart Money Concepts (SMC)
- Shows real-time progress on console
- Handles errors gracefully
- Generates professional reports

Author: Trading System Team
Version: 1.0.0
"""

import sys
import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import traceback

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONSOLE UI UTILITIES
# ============================================================================

def print_banner(text: str, char: str = "=", width: int = 70):
    """Print a formatted banner"""
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def print_section(text: str, width: int = 70):
    """Print a section header"""
    print(f"\n{'-' * width}")
    print(f"  {text}")
    print(f"{'-' * width}")


def print_step(step_num: int, total_steps: int, text: str):
    """Print a step indicator"""
    print(f"\n[{step_num}/{total_steps}] {text}")


def print_progress(symbol: str, timeframe: str, bars: int, status: str = "✅"):
    """Print progress for data collection"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  {timestamp} | {status} {symbol:10s} | {timeframe:5s} | {bars:5d} bars")


def print_result(symbol: str, bias: str, confidence: float):
    """Print analysis result"""
    confidence_emoji = "🟢" if confidence >= 75 else "🟡" if confidence >= 55 else "⚪"
    bias_emoji = "📈" if bias == "BULLISH" else "📉" if bias == "BEARISH" else "➡️"
    print(f"  {confidence_emoji} {symbol:10s} | {bias_emoji} {bias:8s} | {confidence:5.1f}% confidence")


# ============================================================================
# PRODUCTION BOT CLASS
# ============================================================================

class ProductionBot:
    """
    Production-grade trading bot with real-time feedback
    """
    
    def __init__(self, symbols: List[str] = None, timeframes: List[str] = None):
        """
        Initialize production bot
        
        Args:
            symbols: List of trading symbols (default: GBPUSD, XAUUSD, EURUSD)
            timeframes: List of timeframes to analyze (default: D1, H4, H1)
        """
        self.symbols = symbols or ["GBPUSD", "XAUUSD", "EURUSD"]
        self.timeframes = timeframes or ["D1", "H4", "H1"]
        self.data_manager = None
        self.smc_analyzer = None
        self.start_time = None
        
        print_banner("🤖 PRODUCTION MT5 TRADING BOT", "═")
        logger.info("Bot initialized")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Timeframes: {', '.join(self.timeframes)}")
    
    def initialize(self) -> bool:
        """Initialize bot components"""
        print_step(1, 5, "Initializing components...")
        
        try:
            # Import and initialize data manager
            print("  ⏳ Loading DataManager...")
            from data_manager import DataManager
            self.data_manager = DataManager()
            print("  ✅ DataManager loaded")
            
            # Import and initialize SMC analyzer
            print("  ⏳ Loading SMC Analyzer...")
            from smc_analyzer_production import SMCAnalyzer
            self.smc_analyzer = SMCAnalyzer()
            print("  ✅ SMC Analyzer loaded")
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            print(f"  ❌ Initialization failed: {e}")
            logger.error(f"Initialization failed: {e}")
            traceback.print_exc()
            return False
    
    def connect_mt5(self) -> bool:
        """Connect to MetaTrader 5"""
        print_step(2, 5, "Connecting to MetaTrader 5...")
        
        try:
            print(f"  ⏳ Establishing connection...")
            print(f"     Server: {self.data_manager.mt5_server}")
            print(f"     Account: {self.data_manager.mt5_login}")
            
            connected = self.data_manager.connect()
            
            if connected:
                print(f"  ✅ Connected to MT5 successfully!")
                logger.info("MT5 connection established")
                return True
            else:
                print(f"  ❌ Failed to connect to MT5")
                logger.error("MT5 connection failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
            logger.error(f"MT5 connection error: {e}")
            return False
    
    def collect_data(self) -> Dict[str, Dict[str, any]]:
        """Collect data from MT5 for all symbols"""
        print_step(3, 5, "Collecting market data from MT5...")
        
        all_data = {}
        
        print(f"\n  {'Time':8s} | {'Status':2s} {'Symbol':10s} | {'TF':5s} | {'Bars':>5s}")
        print(f"  {'-' * 60}")
        
        for symbol in self.symbols:
            try:
                logger.info(f"Collecting data for {symbol}")
                
                # Collect data for all timeframes
                symbol_data = self.data_manager.get_symbol_data(
                    symbol=symbol,
                    timeframes=self.timeframes,
                    lookback_days=90
                )
                
                # Validate data
                if not symbol_data:
                    print_progress(symbol, "ALL", 0, "❌")
                    logger.warning(f"No data collected for {symbol}")
                    continue
                
                # Store data
                all_data[symbol] = symbol_data
                
                # Print progress for each timeframe
                for tf, df in symbol_data.items():
                    if df is not None and not df.empty:
                        print_progress(symbol, tf, len(df), "✅")
                    else:
                        print_progress(symbol, tf, 0, "⚠️")
                
                logger.info(f"Data collection complete for {symbol}")
                
            except Exception as e:
                print_progress(symbol, "ALL", 0, "❌")
                logger.error(f"Error collecting data for {symbol}: {e}")
                continue
        
        print(f"\n  ✅ Data collection complete: {len(all_data)}/{len(self.symbols)} symbols")
        logger.info(f"Data collection phase complete: {len(all_data)} symbols")
        
        return all_data
    
    def analyze_data(self, all_data: Dict[str, Dict[str, any]]) -> List[Dict]:
        """Analyze data using SMC"""
        print_step(4, 5, "Analyzing market structure (SMC)...")
        
        results = []
        
        print(f"\n  Analyzing {len(all_data)} symbols...")
        print(f"  {'Symbol':10s} | {'Bias':8s} | {'Confidence':>12s}")
        print(f"  {'-' * 40}")
        
        for symbol, data in all_data.items():
            try:
                logger.info(f"Analyzing {symbol}")
                print(f"  ⏳ {symbol:10s} | Analyzing...", end="\r")
                
                # Run SMC analysis
                bias = self.smc_analyzer.analyze(symbol, data)
                
                # Store result
                result = {
                    'symbol': symbol,
                    'bias': bias.direction.value,
                    'confidence': bias.confidence,
                    'confidence_level': bias.confidence_level.value,
                    'bullish_score': bias.bullish_score,
                    'bearish_score': bias.bearish_score,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                results.append(result)
                
                # Print result
                print_result(symbol, bias.direction.value, bias.confidence)
                logger.info(f"Analysis complete for {symbol}: {bias.direction.value} ({bias.confidence:.1f}%)")
                
            except Exception as e:
                print(f"  ❌ {symbol:10s} | Analysis failed: {e}")
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        print(f"\n  ✅ Analysis complete: {len(results)}/{len(all_data)} symbols")
        logger.info(f"Analysis phase complete: {len(results)} results")
        
        return results
    
    def generate_report(self, results: List[Dict]):
        """Generate and save report"""
        print_step(5, 5, "Generating report...")
        
        try:
            import pandas as pd
            
            if not results:
                print("  ⚠️ No results to report")
                return
            
            # Create DataFrame
            df_results = pd.DataFrame(results)
            
            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"bot_results_{timestamp}.csv"
            df_results.to_csv(csv_file, index=False)
            print(f"  ✅ CSV report saved: {csv_file}")
            logger.info(f"Report saved: {csv_file}")
            
            # Print summary
            print(f"\n  📊 Summary:")
            print(f"     Total analyzed: {len(results)}")
            bullish = sum(1 for r in results if r['bias'] == 'BULLISH')
            bearish = sum(1 for r in results if r['bias'] == 'BEARISH')
            neutral = sum(1 for r in results if r['bias'] == 'NEUTRAL')
            print(f"     📈 Bullish: {bullish}")
            print(f"     📉 Bearish: {bearish}")
            print(f"     ➡️ Neutral: {neutral}")
            
            high_conf = sum(1 for r in results if r['confidence'] >= 75)
            print(f"     🟢 High confidence (75%+): {high_conf}")
            
        except Exception as e:
            print(f"  ❌ Report generation failed: {e}")
            logger.error(f"Report generation error: {e}")
    
    def run(self) -> bool:
        """Run the complete bot cycle"""
        self.start_time = time.time()
        
        try:
            # Step 1: Initialize
            if not self.initialize():
                return False
            
            # Step 2: Connect to MT5
            if not self.connect_mt5():
                print("\n❌ Cannot proceed without MT5 connection")
                return False
            
            # Step 3: Collect data
            all_data = self.collect_data()
            
            if not all_data:
                print("\n❌ No data collected - aborting")
                return False
            
            # Step 4: Analyze
            results = self.analyze_data(all_data)
            
            if not results:
                print("\n⚠️ No analysis results generated")
                return False
            
            # Step 5: Report
            self.generate_report(results)
            
            # Success!
            elapsed_time = time.time() - self.start_time
            print_banner(f"✅ BOT COMPLETED SUCCESSFULLY", "═")
            print(f"  ⏱️ Total time: {elapsed_time:.1f} seconds")
            print(f"  📊 Symbols processed: {len(results)}")
            print(f"  ✅ Success!")
            
            logger.info(f"Bot completed successfully in {elapsed_time:.1f}s")
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Bot interrupted by user")
            logger.warning("Bot interrupted by user")
            return False
            
        except Exception as e:
            print(f"\n\n❌ CRITICAL ERROR: {e}")
            logger.error(f"Critical error: {e}")
            traceback.print_exc()
            return False
            
        finally:
            # Cleanup
            if self.data_manager:
                try:
                    self.data_manager.disconnect()
                    print("\n  🔌 Disconnected from MT5")
                except:
                    pass


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    print("\n")
    
    # Default configuration
    symbols = ["GBPUSD", "XAUUSD", "EURUSD"]
    timeframes = ["D1", "H4", "H1"]
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        symbols = sys.argv[1].split(",")
        logger.info(f"Using symbols from command line: {symbols}")
    
    # Create and run bot
    bot = ProductionBot(symbols=symbols, timeframes=timeframes)
    success = bot.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
