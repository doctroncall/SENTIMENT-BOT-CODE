# dashboard.py - FIXED VERSION
import os
import time
from datetime import datetime
import pandas as pd
import traceback
from typing import List, Dict, Optional

# Import system modules (with error handling)
try:
    from data_manager import DataManager, normalize_symbol
except ImportError:
    print("❌ Error importing data_manager")
    raise

try:
    from structure_analyzer import StructureAnalyzer
except ImportError:
    print("❌ Error importing structure_analyzer")
    raise

try:
    from sentiment_engine import SentimentEngine
except ImportError:
    print("❌ Error importing sentiment_engine")
    raise

try:
    from report_generator import ReportGenerator
except ImportError:
    print("❌ Error importing report_generator")
    raise

try:
    from verifier import Verifier
except ImportError:
    print("❌ Error importing verifier")
    raise

try:
    from auto_retrain import AutoRetrain
except ImportError:
    print("❌ Error importing auto_retrain")
    raise

try:
    from status_monitor import get_monitor, log_info, log_success, log_error, log_warning, log_data_fetch, log_analysis
except ImportError:
    print("❌ Error importing status_monitor")
    raise


class Dashboard:
    def __init__(self, symbols: List[str] = None):
        """
        FIXED: Initialize dashboard with better validation
        """
        # FIXED: Normalize symbols at initialization
        self.symbols = [normalize_symbol(s) for s in (symbols or ["GBPUSD", "XAUUSD"])]
        
        # Initialize components
        try:
            log_info("Initializing Dashboard components...")
            self.data_manager = DataManager()
            self.sentiment_engine = SentimentEngine()
            self.report_generator = ReportGenerator()
            self.verifier = Verifier()
            self.retrainer = AutoRetrain()
            self.excel_file = "sentiment_log.xlsx"
            
            print(f"✅ Dashboard initialized for symbols: {', '.join(self.symbols)}")
            log_success(f"Dashboard initialized for symbols: {', '.join(self.symbols)}")
            
        except Exception as e:
            print(f"❌ Error initializing dashboard components: {e}")
            log_error(f"Dashboard initialization failed: {e}")
            raise

    # ------------------------------------------
    # 1️⃣ FIXED: Run Full Analysis Cycle with Better Error Recovery
    # ------------------------------------------
    def run_full_cycle(self):
        """FIXED: Run analysis with per-symbol error recovery"""
        print("\n" + "="*60)
        print("🚀 Starting full analysis cycle...")
        print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print("="*60)
        
        log_analysis(f"Starting full analysis cycle for {len(self.symbols)} symbols")
        
        # Initialize data collection tracker
        try:
            from data_manager import get_collection_status
            tracker = get_collection_status()
            tracker.start_collection(self.symbols)
        except Exception as e:
            print(f"⚠️ Could not initialize collection tracker: {e}")
        
        # CRITICAL FIX: Ensure MT5 connection before starting analysis
        if self.data_manager.use_mt5 and not self.data_manager.is_connected():
            print("\n📡 Connecting to MT5...")
            log_analysis("Establishing MT5 connection")
            try:
                tracker.current_status = "connecting"
            except:
                pass
            connected = self.data_manager.connect()
            if not connected:
                error_msg = "Cannot proceed: MT5 connection failed and no fallback data source available"
                print(f"\n❌ {error_msg}")
                log_error("Analysis aborted", error_msg)
                try:
                    tracker.set_error(error_msg)
                except:
                    pass
                return []
            print("✅ Connected to MT5\n")
        
        results = []
        failed_symbols = []
        
        for symbol in self.symbols:
            print(f"\n{'─'*60}")
            print(f"🔍 Processing {symbol}...")
            print(f"{'─'*60}")
            
            log_analysis(f"Processing {symbol}")
            
            try:
                # Process single symbol
                result = self._process_symbol(symbol)
                
                if result is not None:
                    results.append(result)
                    print(f"✅ {symbol} processed successfully")
                    log_success(f"{symbol} processed successfully")
                else:
                    failed_symbols.append(symbol)
                    print(f"⚠️ {symbol} returned no result")
                    log_warning(f"{symbol} returned no result")
                    
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                traceback.print_exc()
                failed_symbols.append(symbol)
                log_error(f"Error processing {symbol}: {str(e)}")
                # FIXED: Continue with next symbol instead of stopping
                continue

        # Save results
        if results:
            try:
                self._save_to_excel(results)
                print(f"\n{'='*60}")
                print(f"✅ Full cycle completed!")
                print(f"   Successful: {len(results)}/{len(self.symbols)}")
                if failed_symbols:
                    print(f"   Failed: {', '.join(failed_symbols)}")
                print(f"{'='*60}")
                log_success(f"Full cycle completed: {len(results)}/{len(self.symbols)} successful", 
                           f"Failed: {', '.join(failed_symbols) if failed_symbols else 'None'}")
            except Exception as e:
                print(f"❌ Error saving results: {e}")
                log_error(f"Error saving results: {str(e)}")
        else:
            print(f"\n❌ No results generated - all symbols failed")
            log_error("Full cycle failed - no results generated")
            
        return results

    def _process_symbol(self, symbol: str) -> Optional[Dict]:
        """
        FIXED: Process single symbol with comprehensive error handling
        """
        try:
            # Step 1: Fetch data
            print(f"📊 Fetching data for {symbol}...")
            log_data_fetch(f"Fetching data for {symbol} (D1, H4, H1)")
            timeframe_data = self.data_manager.get_symbol_data(
                symbol, 
                timeframes=["D1", "H4", "H1"], 
                lookback_days=250  # FIXED: Increased for EMA_200
            )
            
            if not timeframe_data:
                print(f"❌ No data retrieved for {symbol}")
                log_error(f"No data retrieved for {symbol}")
                return None
            
            log_success(f"Data fetched successfully for {symbol}")
            
            # Use daily data as primary timeframe
            df_daily = timeframe_data.get("D1")
            if df_daily is None or df_daily.empty:
                print(f"⚠️ No daily data for {symbol} - skipping")
                log_warning(f"No daily data for {symbol}")
                return None
            
            # FIXED: Validate DataFrame has required columns
            print(f"   DataFrame shape: {df_daily.shape}")
            print(f"   DataFrame columns: {df_daily.columns.tolist()}")
            print(f"   DataFrame index name: {df_daily.index.name}")
            
            required_cols = ['open', 'high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in df_daily.columns]
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                print(f"   Available columns: {df_daily.columns.tolist()}")
                log_error(f"Missing columns in {symbol} data: {missing_cols}")
                return None
            
            print(f"   ✅ All required columns present")
            
            # FIXED: Validate sufficient data
            if len(df_daily) < 200:
                print(f"⚠️ Insufficient data for {symbol} ({len(df_daily)} bars < 200 required)")
                print(f"   Proceeding with limited indicator accuracy...")
            
            # Step 2: Add technical indicators
            print(f"📈 Calculating technical indicators...")
            df_processed = self._add_technical_indicators(df_daily)
            
            # FIXED: Validate indicators were calculated
            if not self._validate_indicators(df_processed):
                print(f"⚠️ Some indicators could not be calculated for {symbol}")
                print(f"   Proceeding with available indicators...")
            
            # Step 3: Add structure signals
            print(f"🔍 Analyzing market structure...")
            df_processed = self._add_structure_signals(df_processed, timeframe_data)
            
            # Step 4: Add symbol column
            df_processed["Symbol"] = symbol
            
            # Step 5: Generate sentiment record
            print(f"🎯 Computing sentiment...")
            record = self.sentiment_engine.create_summary_record(df_processed)
            
            # Step 6: Generate reports
            print(f"📄 Generating reports...")
            sentiment_data = self._prepare_sentiment_data(record, symbol, timeframe_data)
            self.report_generator.generate_reports(symbol, sentiment_data)
            
            return record
            
        except Exception as e:
            print(f"❌ Error in _process_symbol for {symbol}: {e}")
            traceback.print_exc()
            return None

    # ------------------------------------------
    # 2️⃣ FIXED: Add Technical Indicators with Validation
    # ------------------------------------------
    def _validate_dataframe_structure(self, df: pd.DataFrame, symbol: str) -> bool:
        """Validate that DataFrame has the required structure for analysis"""
        if df is None or df.empty:
            print(f"   ❌ DataFrame is None or empty")
            return False
        
        required_cols = ['open', 'high', 'low', 'close']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            print(f"   ❌ DataFrame missing required columns: {missing}")
            print(f"   Available columns: {df.columns.tolist()}")
            return False
        
        # Check for sufficient data
        if len(df) == 0:
            print(f"   ❌ DataFrame has no rows")
            return False
        
        # Check for valid data types
        for col in required_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                print(f"   ❌ Column {col} is not numeric: {df[col].dtype}")
                return False
        
        return True
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """FIXED: Add EMA, RSI, MACD with proper error handling"""
        df = df.copy()
        
        # Validate input DataFrame
        if not self._validate_dataframe_structure(df, "indicator calculation"):
            print(f"   ❌ Invalid DataFrame structure, cannot calculate indicators")
            # Return DataFrame with default indicator values
            df["EMA_200"] = df["close"].mean() if "close" in df.columns else 0
            df["RSI"] = 50
            df["MACD"] = 0
            df["MACD_Signal"] = 0
            return df
        
        try:
            # EMA 200
            if len(df) >= 200:
                df["EMA_200"] = df["close"].ewm(span=200, adjust=False).mean()
            else:
                # Use shorter EMA if insufficient data
                ema_span = max(50, len(df) // 2)
                print(f"   ⚠️ Using EMA_{ema_span} instead of EMA_200 (insufficient data)")
                df["EMA_200"] = df["close"].ewm(span=ema_span, adjust=False).mean()
            
            # RSI (14-period)
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # Handle division by zero
            rs = gain / loss.replace(0, 1e-10)
            df["RSI"] = 100 - (100 / (1 + rs))
            
            # Fill initial NaN values
            df["RSI"] = df["RSI"].fillna(50)
            
            # MACD (12, 26, 9)
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            
            # Fill initial NaN values
            df["MACD"] = df["MACD"].fillna(0)
            df["MACD_Signal"] = df["MACD_Signal"].fillna(0)
            
            print(f"   ✅ Technical indicators calculated")
            
        except Exception as e:
            print(f"   ❌ Error calculating indicators: {e}")
            import traceback
            traceback.print_exc()
            # Set default values on error
            if "close" in df.columns:
                df["EMA_200"] = df["close"].mean()
            else:
                df["EMA_200"] = 0
            df["RSI"] = 50
            df["MACD"] = 0
            df["MACD_Signal"] = 0
        
        return df

    def _validate_indicators(self, df: pd.DataFrame) -> bool:
        """Validate that indicators were properly calculated"""
        required_indicators = ["EMA_200", "RSI", "MACD", "MACD_Signal"]
        
        for indicator in required_indicators:
            if indicator not in df.columns:
                print(f"   ⚠️ Missing indicator: {indicator}")
                return False
            
            
            # Check for excessive NaN values
            if df[indicator].isna().sum() > len(df) * 0.5:
                print(f"   ⚠️ Indicator {indicator} has >50% NaN values")
                return False
        
        return True

    # ------------------------------------------
    # 3️⃣ FIXED: Add Structure Signals with Error Handling
    # ------------------------------------------
    def _add_structure_signals(self, df_daily: pd.DataFrame, 
                               timeframe_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        FIXED: Analyze structure and create OB_Signal, FVG_Signal columns
        """
        df = df_daily.copy()
        
        # Initialize with neutral signals
        df["OB_Signal"] = 0
        df["FVG_Signal"] = 0
        
        try:
            # Analyze daily structure for order blocks
            print(f"   🔍 Analyzing daily structure...")
            analyzer_daily = StructureAnalyzer(df_daily)
            structure_daily = analyzer_daily.analyze(verbose=False)
            
            # Get latest signals using the improved method
            signals_daily = analyzer_daily.get_latest_signals()
            
            # Apply signals to last row (most recent)
            if signals_daily:
                df.loc[df.index[-1], "OB_Signal"] = signals_daily.get('order_block_signal', 0)
                
                # Broadcast signal to recent rows for consistency
                recent_rows = min(5, len(df))
                df.iloc[-recent_rows:, df.columns.get_loc("OB_Signal")] = signals_daily.get('order_block_signal', 0)
            
            # FIXED: Analyze H4 structure for FVG signals if available
            df_h4 = timeframe_data.get("H4")
            if df_h4 is not None and not df_h4.empty:
                print(f"   🔍 Analyzing H4 structure...")
                analyzer_h4 = StructureAnalyzer(df_h4)
                structure_h4 = analyzer_h4.analyze(verbose=False)
                
                signals_h4 = analyzer_h4.get_latest_signals()
                
                if signals_h4:
                    df.loc[df.index[-1], "FVG_Signal"] = signals_h4.get('fvg_signal', 0)
                    
                    # Broadcast signal to recent rows
                    recent_rows = min(5, len(df))
                    df.iloc[-recent_rows:, df.columns.get_loc("FVG_Signal")] = signals_h4.get('fvg_signal', 0)
            else:
                print(f"   ⚠️ No H4 data available, using daily FVG signals")
                # Fallback to daily FVG signals
                if signals_daily:
                    df.loc[df.index[-1], "FVG_Signal"] = signals_daily.get('fvg_signal', 0)
            
            print(f"   ✅ Structure signals added")
            
        except Exception as e:
            print(f"   ❌ Structure analysis failed: {e}")
            traceback.print_exc()
            # Signals remain at default (0)
        
        return df

    # ------------------------------------------
    # 4️⃣ FIXED: Prepare Sentiment Data for Reporting
    # ------------------------------------------
    def _prepare_sentiment_data(self, record: Dict, symbol: str, 
                                timeframe_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        FIXED: Convert sentiment record to comprehensive report format
        """
        sentiment_data = {
            'final_bias': record['Final Bias'],
            'final_confidence': record['Confidence'],
            'final_score': record['Weighted Score'],
            'ema_bias': record['EMA Bias'],
            'rsi_bias': record['RSI Bias'],
            'macd_bias': record['MACD Bias'],
            'ob_bias': record['OB Bias'],
            'fvg_bias': record['FVG Bias'],
            'scores': {
                'ema_trend': record['EMA Bias'],
                'rsi_momentum': record['RSI Bias'],
                'macd': record['MACD Bias'],
                'order_block': record['OB Bias'],
                'fvg': record['FVG Bias']
            },
            'timeframe_details': {}
        }
        
        # Add timeframe-specific details
        for tf, df in timeframe_data.items():
            if df is not None and not df.empty:
                try:
                    # Get latest close and trend
                    latest_close = df['close'].iloc[-1]
                    ema_present = 'EMA_200' in df.columns if hasattr(df, 'columns') else False
                    
                    if ema_present:
                        ema_value = df['EMA_200'].iloc[-1]
                        trend = "Bullish" if latest_close > ema_value else "Bearish"
                    else:
                        # Use price momentum
                        if len(df) >= 20:
                            recent_avg = df['close'].tail(10).mean()
                            older_avg = df['close'].iloc[-20:-10].mean()
                            trend = "Bullish" if recent_avg > older_avg else "Bearish"
                        else:
                            trend = "Neutral"
                    
                    sentiment_data['timeframe_details'][tf] = {
                        'bias': trend,
                        'confidence': record['Confidence'],
                        'reasons': self._generate_reasons(record, tf)
                    }
                    
                except Exception as e:
                    print(f"   ⚠️ Could not generate details for {tf}: {e}")
        
        # Add structure summary
        sentiment_data['structure_summary'] = {
            'Order Block Bias': f"{record['OB Bias']:+.2f}",
            'FVG Bias': f"{record['FVG Bias']:+.2f}",
            'Trend Context': record.get('Trend_Context', 'unknown'),
            'Analysis Time': record['Analysis_Time']
        }
        
        return sentiment_data

    def _generate_reasons(self, record: Dict, timeframe: str) -> List[str]:
        """Generate human-readable reasons for the bias"""
        reasons = []
        
        # EMA reasons
        if abs(record['EMA Bias']) > 0.5:
            direction = "above" if record['EMA Bias'] > 0 else "below"
            reasons.append(f"Price {direction} EMA 200")
        
        # RSI reasons
        if record['RSI Bias'] > 0.5:
            reasons.append("RSI showing bullish momentum")
        elif record['RSI Bias'] < -0.5:
            reasons.append("RSI showing bearish momentum")
        
        # MACD reasons
        if record['MACD Bias'] > 0.5:
            reasons.append("MACD bullish crossover/momentum")
        elif record['MACD Bias'] < -0.5:
            reasons.append("MACD bearish crossover/momentum")
        
        # Structure reasons
        if record['OB Bias'] > 0:
            reasons.append("Bullish order block detected")
        elif record['OB Bias'] < 0:
            reasons.append("Bearish order block detected")
        
        if record['FVG Bias'] > 0:
            reasons.append("Bullish fair value gap present")
        elif record['FVG Bias'] < 0:
            reasons.append("Bearish fair value gap present")
        
        return reasons if reasons else ["Neutral market conditions"]

    # ------------------------------------------
    # 5️⃣ FIXED: Save to Excel with Better Error Handling
    # ------------------------------------------
    def _save_to_excel(self, results: List[Dict]):
        """FIXED: Save results with duplicate handling"""
        try:
            df_new = pd.DataFrame(results)
            
            if os.path.exists(self.excel_file):
                try:
                    df_old = pd.read_excel(self.excel_file)
                    
                    # FIXED: Remove duplicates for same date/symbol
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    mask = ~((df_old['Date'] == today) & 
                            (df_old['Symbol'].isin(df_new['Symbol'])))
                    
                    df_combined = pd.concat([df_old[mask], df_new], ignore_index=True)
                    
                except Exception as e:
                    print(f"⚠️ Could not read existing Excel file: {e}")
                    df_combined = df_new
            else:
                df_combined = df_new
            
            # Sort by date and symbol
            df_combined = df_combined.sort_values(['Date', 'Symbol'], ascending=[False, True])
            
            # Save to Excel
            df_combined.to_excel(self.excel_file, index=False)
            print(f"\n📊 Saved {len(results)} entries to {self.excel_file}")
            
        except Exception as e:
            print(f"❌ Error saving to Excel: {e}")
            # Try CSV fallback
            try:
                csv_file = self.excel_file.replace('.xlsx', '.csv')
                df_new.to_csv(csv_file, mode='a', 
                             header=not os.path.exists(csv_file), index=False)
                print(f"✅ Saved to CSV fallback: {csv_file}")
            except Exception as e2:
                print(f"❌ CSV fallback also failed: {e2}")

    # ------------------------------------------
    # 6️⃣ FIXED: Run Verification
    # ------------------------------------------
    def run_verification(self):
        """Run verification with error handling"""
        print("\n" + "="*60)
        print("🔍 Running verification process...")
        print("="*60)
        
        try:
            self.verifier.verify_all()
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            traceback.print_exc()

    # ------------------------------------------
    # 7️⃣ FIXED: Run Retraining
    # ------------------------------------------
    def run_retrain(self):
        """Run retraining with error handling"""
        print("\n" + "="*60)
        print("🧠 Running adaptive retraining...")
        print("="*60)
        
        try:
            self.retrainer.run_cycle()
        except Exception as e:
            print(f"❌ Retraining failed: {e}")
            traceback.print_exc()

    # ------------------------------------------
    # 8️⃣ FIXED: Show System Status
    # ------------------------------------------
    def show_status(self):
        """Display comprehensive system status"""
        print("\n" + "="*60)
        print("📊 SYSTEM STATUS SUMMARY")
        print("="*60)
        
        if not os.path.exists(self.excel_file):
            print("⚠️ No sentiment logs available yet.")
            print("Run analysis first: dashboard.run_full_cycle()")
            return

        try:
            df = pd.read_excel(self.excel_file)
            
            # Basic info
            print(f"Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"Tracked Symbols: {', '.join(self.symbols)}")
            print(f"Total Records: {len(df)}")
            
            # Calculate accuracy if verification data exists
            if "Verified" in df.columns:
                verified_mask = df["Verified"].isin(["✅ True", "❌ False"])
                verified_df = df[verified_mask]
                
                if not verified_df.empty:
                    correct = (verified_df["Verified"] == "✅ True").sum()
                    total_verified = len(verified_df)
                    accuracy = (correct / total_verified) * 100
                    
                    print(f"\n📈 Performance Metrics:")
                    print(f"   Total Verified: {total_verified}")
                    print(f"   Correct Predictions: {correct}")
                    print(f"   Accuracy: {accuracy:.1f}%")
                    
                    # By symbol
                    if "Symbol" in verified_df.columns:
                        print(f"\n   By Symbol:")
                        for symbol in verified_df["Symbol"].unique():
                            symbol_df = verified_df[verified_df["Symbol"] == symbol]
                            symbol_correct = (symbol_df["Verified"] == "✅ True").sum()
                            symbol_total = len(symbol_df)
                            symbol_acc = (symbol_correct / symbol_total * 100) if symbol_total > 0 else 0
                            print(f"      {symbol}: {symbol_acc:.1f}% ({symbol_correct}/{symbol_total})")
            
            # Latest entries
            print(f"\n📋 Last 5 Predictions:")
            latest = df.tail(5)
            display_cols = ["Date", "Symbol", "Final Bias", "Confidence"]
            if "Verified" in latest.columns:
                display_cols.append("Verified")
            
            print(latest[display_cols].to_string(index=False))
            
        except Exception as e:
            print(f"❌ Error displaying status: {e}")
            traceback.print_exc()
        
        print("="*60)

    # ------------------------------------------
    # 9️⃣ FIXED: Schedule Automatic Runs
    # ------------------------------------------
    def schedule_daily_runs(self, analysis_hour: int = 5, verify_hour: int = 23):
        """
        FIXED: Schedule with better state management
        """
        print(f"\n🕒 Daily scheduler active")
        print(f"   Analysis: {analysis_hour:02d}:00 UTC")
        print(f"   Verification: {verify_hour:02d}:00 UTC")
        print("   Press Ctrl+C to stop")
        
        last_analysis_date = None
        last_verify_date = None
        
        try:
            while True:
                now = datetime.utcnow()
                current_date = now.date()
                
                # Run analysis
                if (now.hour == analysis_hour and 
                    now.minute < 5 and  # Run within first 5 minutes
                    current_date != last_analysis_date):
                    
                    print(f"\n🔄 Scheduled analysis starting at {now}")
                    self.run_full_cycle()
                    last_analysis_date = current_date
                    time.sleep(300)  # Sleep 5 minutes after run
                
                # Run verification
                elif (now.hour == verify_hour and 
                      now.minute < 5 and
                      current_date != last_verify_date):
                    
                    print(f"\n🔄 Scheduled verification starting at {now}")
                    self.run_verification()
                    self.run_retrain()
                    last_verify_date = current_date
                    time.sleep(300)  # Sleep 5 minutes after run
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Scheduler stopped by user")
        except Exception as e:
            print(f"\n❌ Scheduler error: {e}")
            traceback.print_exc()

    # ------------------------------------------
    # 🔟 NEW: Manual Run Method
    # ------------------------------------------
    def run_manual_analysis(self, symbol: Optional[str] = None):
        """Run analysis for specific symbol or all symbols"""
        if symbol:
            # Normalize and validate symbol
            symbol = normalize_symbol(symbol)
            original_symbols = self.symbols
            self.symbols = [symbol]
            
            print(f"🎯 Running manual analysis for {symbol}")
            self.run_full_cycle()
            
            self.symbols = original_symbols
        else:
            self.run_full_cycle()
        
        self.show_status()

    # ------------------------------------------
    # NEW: Health Check
    # ------------------------------------------
    def health_check(self):
        """Check system component health"""
        print("\n🔍 Running system health check...")
        
        checks = {
            "Data Manager": False,
            "MT5 Connection": False,
            "Excel Log": False,
            "Config Directory": False,
            "Sentiment Engine": False
        }
        
        # Check data manager
        try:
            checks["Data Manager"] = self.data_manager is not None
        except:
            pass
        
        # Check MT5
        try:
            checks["MT5 Connection"] = self.data_manager.is_connected()
        except:
            pass
        
        # Check Excel file
        checks["Excel Log"] = os.path.exists(self.excel_file)
        
        # Check config directory
        checks["Config Directory"] = os.path.exists("config")
        
        # Check sentiment engine
        try:
            checks["Sentiment Engine"] = self.sentiment_engine is not None
        except:
            pass
        
        print("\n📋 Health Check Results:")
        for component, status in checks.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {component}")
        
        all_healthy = all(checks.values())
        if all_healthy:
            print("\n✅ All systems operational")
        else:
            print("\n⚠️ Some systems need attention")
        
        return all_healthy


# Demo execution
if __name__ == "__main__":
    print("🤖 Trading System Dashboard")
    print("="*60)
    
    try:
        dashboard = Dashboard()
        
        print("\n📋 Available Options:")
        print("1. Run full analysis cycle")
        print("2. Show status")
        print("3. Run verification")
        print("4. Run retraining")
        print("5. Start scheduler")
        print("6. Health check")
        print("7. Manual analysis (specific symbol)")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            dashboard.run_full_cycle()
        elif choice == "2":
            dashboard.show_status()
        elif choice == "3":
            dashboard.run_verification()
        elif choice == "4":
            dashboard.run_retrain()
        elif choice == "5":
            print("\nStarting scheduler... Press Ctrl+C to stop")
            dashboard.schedule_daily_runs()
        elif choice == "6":
            dashboard.health_check()
        elif choice == "7":
            symbol = input("Enter symbol (e.g., GBPUSD): ").strip()
            dashboard.run_manual_analysis(symbol)
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()