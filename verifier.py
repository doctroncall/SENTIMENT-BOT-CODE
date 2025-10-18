# verifier.py - FIXED VERSION
import pandas as pd
import datetime
import time
import os
from typing import Optional, Tuple

# Optional MT5 import with fallback
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

# MT5 credentials - read from environment variables with sensible defaults
DEFAULT_MT5_LOGIN = int(os.environ.get("MT5_LOGIN", "0"))
DEFAULT_MT5_PASSWORD = os.environ.get("MT5_PASSWORD", "")
DEFAULT_MT5_SERVER = os.environ.get("MT5_SERVER", "Pepperstone-Demo")

class Verifier:
    def __init__(self, excel_file="sentiment_log.xlsx", mt5_login=None, 
                 mt5_password=None, mt5_server=None):
        self.excel_file = excel_file
        self.mt5_login = mt5_login if mt5_login is not None else DEFAULT_MT5_LOGIN
        self.mt5_password = mt5_password if mt5_password is not None else DEFAULT_MT5_PASSWORD
        self.mt5_server = mt5_server if mt5_server is not None else DEFAULT_MT5_SERVER
        self._initialized = False
        
    def _init_mt5(self) -> bool:
        """Initialize MT5 connection with error handling"""
        if not MT5_AVAILABLE:
            print("❌ MT5 not available for verification")
            return False
            
        if self._initialized:
            return True
            
        try:
            if not mt5.initialize():
                print("❌ MT5 initialization failed")
                return False
                
            if not mt5.login(login=self.mt5_login, password=self.mt5_password, server=self.mt5_server):
                print(f"❌ MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False
                
            self._initialized = True
            print("✅ MT5 connected for verification.")
            return True
            
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            return False

    # ------------------------------------------
    # 1️⃣ IMPROVED: Load Pending Verifications
    # ------------------------------------------
    def load_pending(self) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Load pending verifications with better error handling"""
        if not os.path.exists(self.excel_file):
            print("⚠️ No sentiment log found yet.")
            return None
            
        try:
            df = pd.read_excel(self.excel_file)
            
            # Check if required columns exist
            required_cols = ["Date", "Symbol", "Final Bias", "Verified"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"⚠️ Missing required columns: {missing_cols}")
                return None
                
            # Filter pending verifications
            pending_mask = df["Verified"].isin(["Pending", "pending", "PENDING", None, ""])
            pending = df[pending_mask].copy()
            
            if pending.empty:
                print("✅ No pending verifications.")
                return None
                
            print(f"📋 Found {len(pending)} pending verifications")
            return df, pending
            
        except Exception as e:
            print(f"❌ Error loading pending verifications: {e}")
            return None

    # ------------------------------------------
    # 2️⃣ FIXED: Fetch Price Data for Target Date
    # ------------------------------------------
    def fetch_candles(self, symbol: str, date: str) -> Optional[list]:
        """
        Fetch candle data for verification with fallback.
        Returns candles starting from the prediction date.
        """
        if not self._init_mt5():
            print(f"⚠️ Cannot fetch data for {symbol} - MT5 not available")
            return None
            
        try:
            # Parse prediction date
            prediction_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            
            # FIXED: Check if enough time has passed for verification
            days_elapsed = (datetime.datetime.now() - prediction_date).days
            if days_elapsed < 1:
                print(f"⏳ Prediction from {date} is too recent (need at least 1 day)")
                return None
            
            # Fetch from prediction date + 4 days for safety
            utc_from = prediction_date
            utc_to = prediction_date + datetime.timedelta(days=4)
            
            # Convert to timestamps for MT5
            utc_from_timestamp = int(utc_from.timestamp())
            utc_to_timestamp = int(utc_to.timestamp())
            
            # Normalize symbol (remove special characters)
            symbol = self._normalize_symbol(symbol)
            
            # Fetch daily candles
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_D1, utc_from_timestamp, utc_to_timestamp)
            
            if rates is None or len(rates) < 2:
                print(f"⚠️ Not enough data for {symbol} on {date} (got {len(rates) if rates else 0} candles)")
                return None
                
            print(f"✅ Fetched {len(rates)} candles for {symbol} starting from {date}")
            return rates
            
        except Exception as e:
            print(f"❌ Error fetching candles for {symbol}: {e}")
            return None

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol name for consistent handling"""
        return symbol.upper().replace("/", "").replace("_", "").strip()

    # ------------------------------------------
    # 3️⃣ FIXED: Evaluate Accuracy with Correct Logic
    # ------------------------------------------
    def check_prediction(self, predicted_bias: str, rates: list) -> Tuple[str, bool]:
        """
        Evaluate prediction accuracy with CORRECTED movement calculation.
        
        Logic:
        - rates[0] = Prediction day (the day sentiment was generated)
        - rates[1] = Next day (the day we're verifying against)
        - Movement = next_day_close - prediction_day_close
        
        We verify: Did price move in the predicted direction on the day AFTER prediction?
        """
        if len(rates) < 2:
            return "insufficient_data", False
            
        try:
            # FIXED: Use close-to-close movement for consistency
            prediction_day_close = rates[0]['close']
            next_day_close = rates[1]['close']
            
            # Calculate movement
            movement = next_day_close - prediction_day_close
            movement_pct = (movement / prediction_day_close) * 100 if prediction_day_close > 0 else 0
            
            # IMPROVED: Dynamic threshold based on symbol volatility
            # You can customize this per symbol (e.g., crypto vs forex)
            bias_threshold = 0.05  # 0.05% threshold for neutral
            abs_movement_pct = abs(movement_pct)
            
            # Determine actual bias
            if abs_movement_pct < bias_threshold:
                actual_bias = "neutral"
            elif movement > 0:
                actual_bias = "bullish"
            else:
                actual_bias = "bearish"
                
            # Check prediction accuracy (case-insensitive)
            predicted_lower = predicted_bias.lower().strip()
            result = (predicted_lower == actual_bias)
            
            # Enhanced logging
            print(f"   Prediction Day Close: {prediction_day_close:.5f}")
            print(f"   Next Day Close: {next_day_close:.5f}")
            print(f"   Movement: {movement_pct:+.3f}% → Actual: {actual_bias.upper()}")
            print(f"   Predicted: {predicted_bias.upper()} → {'✅ CORRECT' if result else '❌ INCORRECT'}")
            
            return actual_bias, result
            
        except Exception as e:
            print(f"❌ Error checking prediction: {e}")
            return "error", False

    # ------------------------------------------
    # 4️⃣ IMPROVED: Run Daily Verification
    # ------------------------------------------
    def verify_all(self):
        """Run verification for all pending predictions"""
        data = self.load_pending()
        if data is None:
            return
            
        df, pending = data
        verified_count = 0
        skipped_count = 0
        
        print(f"\n🔍 Starting verification of {len(pending)} predictions...")
        print(f"{'='*60}")
        
        for idx, row in pending.iterrows():
            symbol = row.get("Symbol")
            date = row.get("Date")
            predicted_bias = row.get("Final Bias")
            
            # Skip if essential data is missing
            if pd.isna(symbol) or pd.isna(date) or pd.isna(predicted_bias):
                print(f"⚠️ Skipping row {idx} - missing essential data")
                skipped_count += 1
                continue
            
            # Convert date to string if it's a datetime object
            if isinstance(date, pd.Timestamp):
                date = date.strftime("%Y-%m-%d")
            else:
                date = str(date)
                
            print(f"\n📊 Verifying {symbol} prediction from {date}...")
            print(f"   Predicted: {predicted_bias}")

            # Fetch candles
            rates = self.fetch_candles(symbol, date)
            if rates is None:
                # Mark as unable to verify
                df.loc[idx, "Verified"] = "Unable to Verify"
                df.loc[idx, "Actual Bias"] = "No Data"
                df.loc[idx, "Close Movement"] = 0
                df.loc[idx, "Movement_Pct"] = 0
                skipped_count += 1
                continue

            # Check prediction
            actual_bias, result = self.check_prediction(predicted_bias, rates)
            
            # FIXED: Calculate movement correctly
            movement = rates[1]['close'] - rates[0]['close']
            movement_pct = (movement / rates[0]['close']) * 100 if rates[0]['close'] > 0 else 0
            
            # Update DataFrame
            df.loc[idx, "Verified"] = "✅ True" if result else "❌ False"
            df.loc[idx, "Actual Bias"] = actual_bias.capitalize()
            df.loc[idx, "Close Movement"] = round(movement, 5)
            df.loc[idx, "Movement_Pct"] = round(movement_pct, 3)
            df.loc[idx, "Verification_Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            df.loc[idx, "Prediction_Close"] = rates[0]['close']
            df.loc[idx, "Next_Day_Close"] = rates[1]['close']
            
            verified_count += 1
            
            print(f"   Result: {df.loc[idx, 'Verified']}")
            print(f"{'-'*60}")

        # Save updated DataFrame
        try:
            df.to_excel(self.excel_file, index=False)
            print(f"\n{'='*60}")
            print(f"✅ Verification complete!")
            print(f"   Verified: {verified_count}")
            print(f"   Skipped: {skipped_count}")
            print(f"{'='*60}")
            
            # Print summary
            if verified_count > 0:
                self._print_verification_summary(df)
            
        except Exception as e:
            print(f"❌ Error saving verification results: {e}")

    def _print_verification_summary(self, df: pd.DataFrame):
        """Print verification summary statistics"""
        verified_df = df[df["Verified"].isin(["✅ True", "❌ False"])]
        
        if verified_df.empty:
            print("📊 No verified predictions to summarize.")
            return
            
        total_verified = len(verified_df)
        correct_predictions = len(verified_df[verified_df["Verified"] == "✅ True"])
        accuracy = (correct_predictions / total_verified) * 100 if total_verified > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"📈 VERIFICATION SUMMARY:")
        print(f"{'='*60}")
        print(f"   Total Verified: {total_verified}")
        print(f"   Correct: {correct_predictions}")
        print(f"   Incorrect: {total_verified - correct_predictions}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        # Accuracy by symbol
        if "Symbol" in verified_df.columns:
            print(f"\n   Accuracy by Symbol:")
            symbol_stats = verified_df.groupby("Symbol").agg({
                'Verified': lambda x: (x == "✅ True").sum(),
                'Symbol': 'count'
            })
            symbol_stats.columns = ['Correct', 'Total']
            symbol_stats['Accuracy %'] = (symbol_stats['Correct'] / symbol_stats['Total'] * 100).round(1)
            
            for symbol, row in symbol_stats.iterrows():
                print(f"     {symbol}: {row['Accuracy %']:.1f}% ({int(row['Correct'])}/{int(row['Total'])})")
        
        # Bias distribution
        if "Final Bias" in verified_df.columns:
            print(f"\n   Accuracy by Bias:")
            bias_stats = verified_df.groupby("Final Bias").agg({
                'Verified': lambda x: (x == "✅ True").sum(),
                'Final Bias': 'count'
            })
            bias_stats.columns = ['Correct', 'Total']
            bias_stats['Accuracy %'] = (bias_stats['Correct'] / bias_stats['Total'] * 100).round(1)
            
            for bias, row in bias_stats.iterrows():
                print(f"     {bias}: {row['Accuracy %']:.1f}% ({int(row['Correct'])}/{int(row['Total'])})")
        
        print(f"{'='*60}\n")

    # ------------------------------------------
    # 5️⃣ IMPROVED: Auto-Scheduler with Timing Check
    # ------------------------------------------
    def schedule_daily(self, verification_hour: int = 0, verification_minute: int = 10):
        """Run daily verification at specified time"""
        print(f"🕒 Waiting until {verification_hour:02d}:{verification_minute:02d} UTC to verify predictions...")
        
        last_run_date = None
        
        while True:
            now = datetime.datetime.utcnow()
            current_date = now.date()
            
            # Check if it's time to verify (once per day)
            if (now.hour == verification_hour and 
                now.minute >= verification_minute and 
                current_date != last_run_date):
                
                print(f"\n🔄 Running scheduled verification at {now}")
                self.verify_all()
                last_run_date = current_date
                
                # Wait a bit to avoid multiple runs
                print("✅ Daily verification done. Sleeping...")
                time.sleep(3600)  # Sleep 1 hour after run
                
            time.sleep(60)  # Check every minute

    # ------------------------------------------
    # 6️⃣ IMPROVED: Manual Verification with Enhanced Output
    # ------------------------------------------
    def verify_manual(self, symbol: str, date: str, predicted_bias: str):
        """Manually verify a specific prediction"""
        print(f"\n{'='*60}")
        print(f"🔍 Manual verification for {symbol} on {date}")
        print(f"{'='*60}")
        
        rates = self.fetch_candles(symbol, date)
        if rates is None:
            print("❌ Could not fetch data for manual verification")
            return None
            
        actual_bias, result = self.check_prediction(predicted_bias, rates)
        
        print(f"\n{'='*60}")
        print(f"📊 RESULT: Prediction was {'✅ CORRECT' if result else '❌ INCORRECT'}")
        print(f"   Predicted: {predicted_bias.upper()}")
        print(f"   Actual: {actual_bias.upper()}")
        print(f"{'='*60}\n")
        
        return result


# Test function
if __name__ == "__main__":
    print("🧪 Testing Verifier...")
    
    verifier = Verifier()
    
    # Test with sample data (adjust date to a past date for real testing)
    test_result = verifier.verify_manual("GBPUSD", "2024-01-15", "bullish")
    print(f"Test completed: {test_result}")