# sentiment_engine.py - FIXED VERSION
import json
import numpy as np
import pandas as pd
from datetime import datetime
import os
from typing import Dict, Tuple, Optional

class SentimentEngine:
    def __init__(self, weights_file="config/rule_weights.json"):
        self.weights_file = weights_file
        self.weights = self.load_weights()
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        config_dir = os.path.dirname(self.weights_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            print(f"✅ Created config directory: {config_dir}")

    # ------------------------------------------
    # 1️⃣ IMPROVED: Load adaptive rule weights
    # ------------------------------------------
    def load_weights(self):
        try:
            with open(self.weights_file, "r") as f:
                weights = json.load(f)
                print("✅ Loaded adaptive rule weights:", weights)
                return weights
        except FileNotFoundError:
            print("⚠️ No weights file found. Creating default weights.")
            weights = self._get_default_weights()
            # Save default weights
            try:
                with open(self.weights_file, "w") as f:
                    json.dump(weights, f, indent=4)
                print("✅ Created default weights file")
            except Exception as e:
                print(f"⚠️ Could not create weights file: {e}")
            return weights
        except json.JSONDecodeError:
            print("❌ Corrupted weights file. Using defaults.")
            return self._get_default_weights()

    def _get_default_weights(self):
        """Return default weights as fallback"""
        return {
            "ema_trend_weight": 0.25,
            "rsi_momentum_weight": 0.20,
            "macd_weight": 0.15,
            "order_block_weight    # ------------------------------------------
    # 2️⃣ FIXED: Compute Indicator Bias Scores with Context
    # ------------------------------------------
    def compute_indicator_bias(self, df):
        """
        FIXED: Compute bias scores with trend context and improved logic
        Expects DataFrame with required columns.
        """
        if df is None or df.empty:
            raise ValueError("❌ Empty DataFrame provided to sentiment engine")

        # Validate required columns with better error handling
        required_columns = ["close", "EMA_200", "RSI", "MACD", "MACD_Signal", "OB_Signal", "FVG_Signal"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠️ Missing columns: {missing_columns}. Using defaults where possible.")
            # Set default values for missing columns
            for col in missing_columns:
                if col == "EMA_200":
                    df[col] = df["close"].rolling(window=min(200, len(df))).mean()
                elif col == "RSI":
                    df[col] = 50  # Neutral RSI
                elif col in ["MACD", "MACD_Signal"]:
                    df[col] = 0
                elif col in ["OB_Signal", "FVG_Signal"]:
                    df[col] = 0eError(f"❌ Missing required columns: {missing_columns}")

        bias_scores = {}

        try:
            # Get current and historical data for context
            current_close = df["close"].iloc[-1]
            prev_close = df["close"].iloc[-2] if len(df) > 1 else current_close
            
            # FIXED: Determine overall trend context first
            trend_context = self._determine_trend_context(df)

            # ============================================
            # 1. EMA Trend Bias (200-period)
            # ============================================
            current_ema = df["EMA_200"].iloc[-1]
            
            if pd.isna(current_ema):
                # If EMA not calculated, use price position relative to recent average
                recent_avg = df["close"].tail(20).mean()
                ema_bias = 1 if current_close > recent_avg else -1
                distance_pct = abs(current_close - recent_avg) / recent_avg if recent_avg > 0 else 0
            else:
                ema_bias = 1 if current_close > current_ema else -1
                distance_pct = abs(current_close - current_ema) / current_ema if current_ema > 0 else 0
            
            # FIXED: Add strength based on distance and trend consistency
            if distance_pct > 0.03:  # 3% distance - strong signal
                ema_bias *= 1.0
            elif distance_pct > 0.01:  # 1% distance - moderate signal
                ema_bias *= 0.8
            else:  # Close to EMA - weak signal
                ema_bias *= 0.5
                    
            bias_scores["ema_trend"] = np.clip(ema_bias, -1, 1)

            # ============================================
            # 2. FIXED: RSI Momentum Bias with Trend Context
            # ============================================
            rsi = df["RSI"].iloc[-1]
            prev_rsi = df["RSI"].iloc[-2] if len(df) > 1 else rsi
            
            if pd.isna(rsi):
                bias_scores["rsi_momentum"] = 0
            else:
                # FIXED: Context-aware RSI interpretation
                if trend_context == "uptrend":
                    # In uptrend, RSI > 50 is bullish, RSI < 30 is oversold (buy opportunity)
                    if rsi > 70:
                        bias_scores["rsi_momentum"] = 0.5  # Overbought in uptrend = moderate bullish
                    elif rsi > 55:
                        bias_scores["rsi_momentum"] = 1.0  # Strong bullish momentum
                    elif rsi > 40:
                        bias_scores["rsi_momentum"] = 0.3  # Weak bullish
                    elif rsi > 30:
                        bias_scores["rsi_momentum"] = -0.3  # Pullback
                    else:
                        bias_scores["rsi_momentum"] = 0.8  # Oversold in uptrend = buying opportunity
                        
                elif trend_context == "downtrend":
                    # In downtrend, RSI < 50 is bearish, RSI > 70 is overbought (sell opportunity)
                    if rsi < 30:
                        bias_scores["rsi_momentum"] = -0.5  # Oversold in downtrend = moderate bearish
                    elif rsi < 45:
                        bias_scores["rsi_momentum"] = -1.0  # Strong bearish momentum
                    elif rsi < 60:
                        bias_scores["rsi_momentum"] = -0.3  # Weak bearish
                    elif rsi < 70:
                        bias_scores["rsi_momentum"] = 0.3  # Rally
                    else:
                        bias_scores["rsi_momentum"] = -0.8  # Overbought in downtrend = selling opportunity
                        
                else:  # neutral/ranging
                    # In ranging market, use traditional levels
                    if rsi > 70:
                        bias_scores["rsi_momentum"] = -0.8  # Overbought
                    elif rsi > 60:
                        bias_scores["rsi_momentum"] = 0.3
                    elif rsi < 30:
                        bias_scores["rsi_momentum"] = 0.8  # Oversold
                    elif rsi < 40:
                        bias_scores["rsi_momentum"] = -0.3
                    else:
                        bias_scores["rsi_momentum"] = 0  # Neutral
                
                # FIXED: Consider RSI momentum (direction of change)
                rsi_momentum = rsi - prev_rsi
                if abs(rsi_momentum) > 5:  # Strong momentum change
                    momentum_boost = 0.2 if rsi_momentum > 0 else -0.2
                    bias_scores["rsi_momentum"] = np.clip(
                        bias_scores["rsi_momentum"] + momentum_boost, -1, 1
                    )

            # ============================================
            # 3. FIXED: MACD Signal Bias with Histogram
            # ============================================
            macd = df["MACD"].iloc[-1]
            macd_signal = df["MACD_Signal"].iloc[-1]
            
            if pd.isna(macd) or pd.isna(macd_signal):
                bias_scores["macd"] = 0
            else:
                macd_histogram = macd - macd_signal
                prev_macd = df["MACD"].iloc[-2] if len(df) > 1 else macd
                prev_signal = df["MACD_Signal"].iloc[-2] if len(df) > 1 else macd_signal
                prev_histogram = prev_macd - prev_signal
                
                # FIXED: Consider crossover, position, and momentum
                # Crossover detection
                bullish_cross = prev_histogram <= 0 and macd_histogram > 0
                bearish_cross = prev_histogram >= 0 and macd_histogram < 0
                
                # Histogram momentum (is it expanding or contracting?)
                histogram_momentum = macd_histogram - prev_histogram
                
                if bullish_cross:
                    bias_scores["macd"] = 1.0  # Fresh bullish crossover
                elif bearish_cross:
                    bias_scores["macd"] = -1.0  # Fresh bearish crossover
                elif macd_histogram > 0:
                    # Above zero - bullish territory
                    if histogram_momentum > 0:
                        bias_scores["macd"] = 0.7  # Expanding bullish
                    else:
                        bias_scores["macd"] = 0.3  # Contracting bullish
                elif macd_histogram < 0:
                    # Below zero - bearish territory
                    if histogram_momentum < 0:
                        bias_scores["macd"] = -0.7  # Expanding bearish
                    else:
                        bias_scores["macd"] = -0.3  # Contracting bearish
                else:
                    bias_scores["macd"] = 0

            # ============================================
            # 4. Order Block Bias (from structure analyzer)
            # ============================================
            ob_signal = df["OB_Signal"].iloc[-1]
            if pd.isna(ob_signal):
                bias_scores["order_block"] = 0
            else:
                # Order blocks are weighted by their alignment with trend
                if trend_context == "uptrend" and ob_signal > 0:
                    bias_scores["order_block"] = ob_signal * 1.2  # Boost aligned signals
                elif trend_context == "downtrend" and ob_signal < 0:
                    bias_scores["order_block"] = ob_signal * 1.2
                else:
                    bias_scores["order_block"] = ob_signal * 0.8  # Reduce counter-trend signals
                
                bias_scores["order_block"] = np.clip(bias_scores["order_block"], -1, 1)

            # ============================================
            # 5. FVG Bias (from structure analyzer)
            # ============================================
            fvg_signal = df["FVG_Signal"].iloc[-1]
            if pd.isna(fvg_signal):
                bias_scores["fvg"] = 0
            else:
                # Similar to order blocks, weight by trend alignment
                if trend_context == "uptrend" and fvg_signal > 0:
                    bias_scores["fvg"] = fvg_signal * 1.2
                elif trend_context == "downtrend" and fvg_signal < 0:
                    bias_scores["fvg"] = fvg_signal * 1.2
                else:
                    bias_scores["fvg"] = fvg_signal * 0.8
                
                bias_scores["fvg"] = np.clip(bias_scores["fvg"], -1, 1)

        except Exception as e:
            print(f"❌ Error computing indicator biases: {e}")
            # Return neutral biases on error
            bias_scores = {
                "ema_trend": 0,
                "rsi_momentum": 0,
                "macd": 0,
                "order_block": 0,
                "fvg": 0
            }

        return bias_scores

    def _determine_trend_context(self, df) -> str:
        """
        FIXED: Determine overall trend context for better indicator interpretation
        """
        if len(df) < 50:
            return "neutral"
        
        try:
            current_close = df["close"].iloc[-1]
            ema_200 = df["EMA_200"].iloc[-1]
            
            # Price position relative to EMA
            if not pd.isna(ema_200):
                if current_close > ema_200 * 1.01:  # 1% above
                    # Check if recent trend is up
                    recent_close_avg = df["close"].tail(10).mean()
                    older_close_avg = df["close"].iloc[-20:-10].mean()
                    
                    if recent_close_avg > older_close_avg:
                        return "uptrend"
                    else:
                        return "neutral"
                        
                elif current_close < ema_200 * 0.99:  # 1% below
                    # Check if recent trend is down
                    recent_close_avg = df["close"].tail(10).mean()
                    older_close_avg = df["close"].iloc[-20:-10].mean()
                    
                    if recent_close_avg < older_close_avg:
                        return "downtrend"
                    else:
                        return "neutral"
            
            return "neutral"
            
        except Exception as e:
            print(f"⚠️ Error determining trend context: {e}")
            return "neutral"

    # ------------------------------------------
    # 3️⃣ FIXED: Compute Weighted Sentiment with Better Confidence
    # ------------------------------------------
    def compute_weighted_sentiment(self, df):
        """FIXED: Compute final sentiment score with improved confidence calculation"""
        try:
            scores = self.compute_indicator_bias(df)
            
            # Calculate weighted sum
            weighted_sum = 0
            total_weight = sum(self.weights.values())
            
            if total_weight == 0:
                print("⚠️ Zero total weight, using equal weights")
                self.weights = {k: 0.2 for k in self.weights}
                total_weight = 1.0

            for key, weight in self.weights.items():
                indicator_key = key.replace("_weight", "")
                if indicator_key in scores:
                    score = scores[indicator_key]
                    weighted_sum += weight * score
                else:
                    print(f"⚠️ Missing score for {indicator_key}")

            final_score = weighted_sum / total_weight
            
            # FIXED: Calculate confidence using improved algorithm
            confidence = self._calculate_confidence(final_score, scores)
            
            # Determine bias with dynamic thresholds
            bias = self._determine_bias(final_score, confidence, scores)
            
            self._print_sentiment_summary(df, scores, final_score, bias, confidence)
            
            return bias, confidence, scores, final_score
            
        except Exception as e:
            print(f"❌ Error in sentiment calculation: {e}")
            return "Neutral", 0.0, {}, 0.0

    def _calculate_confidence(self, final_score: float, scores: Dict[str, float]) -> float:
        """
        FIXED: Calculate confidence using sigmoid-based approach
        Considers both score magnitude and indicator agreement
        """
        # Component 1: Score magnitude (how strong is the signal?)
        # Use sigmoid function for smooth scaling
        score_strength = abs(final_score)
        magnitude_confidence = 1 / (1 + np.exp(-10 * (score_strength - 0.3)))
        
        # Component 2: Indicator agreement (how many agree?)
        score_values = list(scores.values())
        
        if not score_values:
            return 0.0
        
        # Calculate agreement: what % of indicators point same direction?
        positive_count = sum(1 for s in score_values if s > 0.1)
        negative_count = sum(1 for s in score_values if s < -0.1)
        neutral_count = len(score_values) - positive_count - negative_count
        
        total_indicators = len(score_values)
        max_directional = max(positive_count, negative_count)
        
        # Agreement ratio
        agreement_ratio = max_directional / total_indicators if total_indicators > 0 else 0
        
        # Boost confidence if most indicators agree
        if agreement_ratio >= 0.8:  # 80%+ agreement
            agreement_confidence = 1.0
        elif agreement_ratio >= 0.6:  # 60-80% agreement
            agreement_confidence = 0.7
        else:
            agreement_confidence = 0.4
        
        # Component 3: Conviction (how strong are the individual signals?)
        # Average absolute strength of all indicators
        conviction = np.mean([abs(s) for s in score_values])
        conviction_confidence = min(conviction * 1.5, 1.0)
        
        # FIXED: Combine components with weights
        final_confidence = (
            magnitude_confidence * 0.4 +
            agreement_confidence * 0.4 +
            conviction_confidence * 0.2
        )
        
        # Cap confidence at reasonable maximum
        return min(round(final_confidence, 3), 0.95)

    def _determine_bias(self, final_score: float, confidence: float, scores: Dict[str, float]) -> str:
        """
        FIXED: Determine bias with dynamic thresholds based on confidence
        """
        # FIXED: Very low confidence = always neutral
        if confidence < 0.25:
            return "Neutral"
        
        # FIXED: Dynamic thresholds based on confidence
        if confidence > 0.75:  # High confidence - lower threshold needed
            bullish_threshold = 0.15
            bearish_threshold = -0.15
        elif confidence > 0.5:  # Medium confidence
            bullish_threshold = 0.25
            bearish_threshold = -0.25
        else:  # Lower confidence - higher threshold needed
            bullish_threshold = 0.35
            bearish_threshold = -0.35
        
        # Determine bias
        if final_score >= bullish_threshold:
            return "Bullish"
        elif final_score <= bearish_threshold:
            return "Bearish"
        else:
            return "Neutral"

    def _print_sentiment_summary(self, df, scores, final_score, bias, confidence):
        """Print detailed sentiment summary"""
        symbol = df.get("Symbol", ["Unknown"]).iloc[-1] if "Symbol" in df.columns else "Unknown"
        
        print(f"\n{'='*50}")
        print(f"📊 SENTIMENT ANALYSIS SUMMARY")
        print(f"{'='*50}")
        print(f"Symbol: {symbol}")
        print(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"{'-'*50}")
        
        for indicator, score in scores.items():
            indicator_name = indicator.replace('_', ' ').title()
            
            # Visual representation
            if score > 0.5:
                arrow = "🟢🟢"
            elif score > 0:
                arrow = "🟢"
            elif score < -0.5:
                arrow = "🔴🔴"
            elif score < 0:
                arrow = "🔴"
            else:
                arrow = "⚪"
                
            print(f" {arrow} {indicator_name:20}: {score:+.3f}")
        
        print(f"{'-'*50}")
        print(f" Final Score: {final_score:+.3f}")
        
        # Visual bias representation
        if bias == "Bullish":
            bias_icon = "🚀"
        elif bias == "Bearish":
            bias_icon = "📉"
        else:
            bias_icon = "↔️"
        
        print(f" Bias: {bias_icon} {bias.upper()}")
        print(f" Confidence: {'█' * int(confidence * 10)}{confidence:.1%}")
        print(f"{'='*50}")

    # ------------------------------------------
    # 4️⃣ IMPROVED: Generate Output Row (for Excel)
    # ------------------------------------------
    def create_summary_record(self, df):
        """Create standardized summary record for logging"""
        try:
            bias, confidence, scores, final_score = self.compute_weighted_sentiment(df)
            
            record = {
                "Date": datetime.utcnow().strftime("%Y-%m-%d"),
                "Symbol": df["Symbol"].iloc[-1] if "Symbol" in df.columns else "Unknown",
                "Final Bias": bias,
                "Confidence": confidence,
                "Weighted Score": round(final_score, 4),
                "EMA Bias": round(scores.get("ema_trend", 0), 3),
                "RSI Bias": round(scores.get("rsi_momentum", 0), 3),
                "MACD Bias": round(scores.get("macd", 0), 3),
                "OB Bias": round(scores.get("order_block", 0), 3),
                "FVG Bias": round(scores.get("fvg", 0), 3),
                "Verified": "Pending",
                "Analysis_Time": datetime.utcnow().strftime("%H:%M:%S"),
                "Trend_Context": self._determine_trend_context(df)
            }
            
            return record
            
        except Exception as e:
            print(f"❌ Error creating summary record: {e}")
            import traceback
            traceback.print_exc()
            
            # Return minimal record on error
            return {
                "Date": datetime.utcnow().strftime("%Y-%m-%d"),
                "Symbol": "Error",
                "Final Bias": "Error",
                "Confidence": 0,
                "Weighted Score": 0,
                "EMA Bias": 0,
                "RSI Bias": 0,
                "MACD Bias": 0,
                "OB Bias": 0,
                "FVG Bias": 0,
                "Verified": "Error",
                "Analysis_Time": datetime.utcnow().strftime("%H:%M:%S"),
                "Trend_Context": "unknown"
            }

    # ------------------------------------------
    # 5️⃣ NEW: Update Weights Manually
    # ------------------------------------------
    def update_weights(self, new_weights):
        """Update rule weights manually"""
        try:
            # Validate weights
            if not isinstance(new_weights, dict):
                raise ValueError("Weights must be a dictionary")
            
            if abs(sum(new_weights.values()) - 1.0) > 0.01:
                print("⚠️ Weights don't sum to 1.0, normalizing...")
                total = sum(new_weights.values())
                new_weights = {k: v/total for k, v in new_weights.items()}
            
            self.weights = new_weights
            
            # Save to file
            with open(self.weights_file, "w") as f:
                json.dump(new_weights, f, indent=4)
            
            print("✅ Weights updated and saved:", new_weights)
            
        except Exception as e:
            print(f"❌ Error updating weights: {e}")

    # ------------------------------------------
    # 6️⃣ NEW: Get Current Configuration
    # ------------------------------------------
    def get_configuration(self):
        """Return current engine configuration"""
        return {
            "weights": self.weights.copy(),
            "weights_file": self.weights_file,
            "default_weights": self._get_default_weights()
        }


# Test function
if __name__ == "__main__":
    # Test the sentiment engine with sample data
    print("🧪 Testing Sentiment Engine...")
    
    # Create sample DataFrame with realistic trending data
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
    np.random.seed(42)
    
    # Create uptrend
    trend = np.linspace(0, 0.1, 250)
    noise = np.random.randn(250) * 0.005
    returns = trend + noise
    prices = 1.2000 * (1 + np.cumsum(returns))
    
    sample_df = pd.DataFrame({
        'close': prices,
        'EMA_200': prices * 0.98,  # EMA below price (uptrend)
        'RSI': 45 + np.random.randn(250) * 10,
        'MACD': np.cumsum(np.random.randn(250) * 0.0001),
        'MACD_Signal': np.cumsum(np.random.randn(250) * 0.00008),
        'OB_Signal': np.random.choice([1, 0, 0], 250),  # More bullish OBs
        'FVG_Signal': np.random.choice([1, 0, -1], 250),
        'Symbol': ['GBPUSD'] * 250
    }, index=dates)
    
    # Ensure RSI in valid range
    sample_df['RSI'] = np.clip(sample_df['RSI'], 20, 80)
    
    engine = SentimentEngine()
    
    # Test sentiment calculation
    try:
        bias, confidence, scores, final_score = engine.compute_weighted_sentiment(sample_df)
        print(f"\n🎯 Test Result: {bias} (Confidence: {confidence:.1%})")
        
        # Test record creation
        record = engine.create_summary_record(sample_df)
        print(f"\n📝 Sample Record:")
        for key, value in record.items():
            print(f"   {key}: {value}")
        
        print("\n✅ SentimentEngine test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()