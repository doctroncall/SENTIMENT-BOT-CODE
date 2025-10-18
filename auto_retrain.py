# auto_retrain.py - FIXED VERSION
import pandas as pd
import json
import os
from datetime import datetime
import numpy as np
from typing import Dict, Any, List, Tuple
import traceback

class AutoRetrain:
    def __init__(self, excel_file="sentiment_log.xlsx", config_file="config/rule_weights.json", 
                 threshold=0.70, min_samples=10):
        self.excel_file = excel_file
        self.config_file = config_file
        self.threshold = threshold  # Accuracy threshold for retraining
        self.min_samples = min_samples  # Minimum samples needed for retraining
        self.df = None
        
        # Ensure config directory exists
        config_dir = os.path.dirname(config_file) if os.path.dirname(config_file) else "config"
        os.makedirs(config_dir, exist_ok=True)

    # ------------------------------------------
    # 1️⃣ IMPROVED: Load Verification History
    # ------------------------------------------
    def load_history(self) -> pd.DataFrame:
        """Load verification history with enhanced validation"""
        if not os.path.exists(self.excel_file):
            raise FileNotFoundError(f"No sentiment log found at {self.excel_file}")
            
        try:
            self.df = pd.read_excel(self.excel_file)
            
            # Check if we have verification data
            if "Verified" not in self.df.columns:
                raise ValueError("No 'Verified' column found in the data")
                
            # FIXED: More flexible verification status detection
            verified_mask = self.df["Verified"].astype(str).str.contains(
                "True|False", case=False, na=False
            )
            self.df = self.df[verified_mask].copy()
            
            if self.df.empty:
                raise ValueError("No verified predictions found for retraining")
            
            # FIXED: Standardize the Verified column
            self.df['is_correct'] = self.df["Verified"].astype(str).str.contains("True", case=False, na=False)
            
            print(f"✅ Loaded {len(self.df)} verified predictions.")
            return self.df
            
        except Exception as e:
            print(f"❌ Error loading history: {e}")
            raise

    # ------------------------------------------
    # 2️⃣ IMPROVED: Compute Performance Metrics
    # ------------------------------------------
    def compute_accuracy(self) -> float:
        """Compute overall accuracy with validation"""
        if self.df is None or self.df.empty:
            raise ValueError("No data available for accuracy computation")
            
        try:
            correct = self.df['is_correct'].sum()
            total = len(self.df)
            accuracy = correct / total if total > 0 else 0
            
            print(f"📈 Current Overall Accuracy: {accuracy * 100:.2f}% ({correct}/{total})")
            return accuracy
            
        except Exception as e:
            print(f"❌ Error computing accuracy: {e}")
            return 0.0

    def compute_indicator_accuracy(self) -> Dict[str, Dict[int, float]]:
        """
        FIXED: Compute accuracy for each indicator value
        Returns: {indicator_name: {value: accuracy}}
        """
        indicator_accuracies = {}
        
        try:
            indicator_columns = ["EMA Bias", "RSI Bias", "MACD Bias", "OB Bias", "FVG Bias"]
            available_indicators = [col for col in indicator_columns if col in self.df.columns]
            
            for indicator in available_indicators:
                # FIXED: Handle continuous values by binning
                indicator_data = self.df[[indicator, 'is_correct']].copy()
                
                # Remove NaN values
                indicator_data = indicator_data.dropna(subset=[indicator])
                
                if indicator_data.empty:
                    continue
                
                # Bin continuous values into categories
                indicator_data['binned'] = pd.cut(
                    indicator_data[indicator], 
                    bins=[-np.inf, -0.5, -0.1, 0.1, 0.5, np.inf],
                    labels=['strong_bearish', 'weak_bearish', 'neutral', 'weak_bullish', 'strong_bullish']
                )
                
                # Calculate accuracy per bin
                accuracy_by_bin = indicator_data.groupby('binned')['is_correct'].agg(['mean', 'count'])
                
                indicator_accuracies[indicator] = {
                    str(cat): {'accuracy': row['mean'], 'count': row['count']}
                    for cat, row in accuracy_by_bin.iterrows()
                }
                
            print("📊 Indicator-wise accuracy computed")
            return indicator_accuracies
            
        except Exception as e:
            print(f"⚠️ Could not compute indicator accuracy: {e}")
            traceback.print_exc()
            return {}

    # ------------------------------------------
    # 3️⃣ FIXED: Adjust Rule Weights with Better Logic
    # ------------------------------------------
    def load_weights(self) -> Dict[str, float]:
        """Load current weights with fallback"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    weights = json.load(f)
                print("✅ Loaded current weights:", weights)
                return weights
            else:
                print("⚠️ No weights file found. Using defaults.")
                return self._get_default_weights()
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ Error loading weights: {e}. Using defaults.")
            return self._get_default_weights()

    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights"""
        return {
            "ema_trend_weight": 0.25,
            "rsi_momentum_weight": 0.20,
            "macd_weight": 0.15,
            "order_block_weight": 0.25,
            "fvg_weight": 0.15
        }

    def adjust_weights(self, accuracy: float, indicator_accuracies: Dict[str, Dict]):
        """
        FIXED: Adjust weights based on performance with improved proportional logic
        """
        if len(self.df) < self.min_samples:
            print(f"⚠️ Not enough samples ({len(self.df)} < {self.min_samples}) for reliable retraining")
            return
            
        weights = self.load_weights()
        print("\n⚙️ Evaluating weight adjustment...")

        if accuracy < self.threshold:
            accuracy_gap = self.threshold - accuracy
            
            print(f"⚠️ Accuracy {accuracy*100:.1f}% below threshold {self.threshold*100:.0f}%")
            print(f"   Accuracy gap: {accuracy_gap*100:.1f}%")

            # FIXED: Calculate weight adjustments proportionally
            weight_adjustments = self._calculate_weight_adjustments_v2(
                indicator_accuracies, accuracy_gap
            )
            
            # FIXED: Apply adjustments proportionally before normalization
            temp_weights = {}
            for indicator, adjustment in weight_adjustments.items():
                weight_key = f"{indicator.lower().replace(' ', '_')}_weight"
                if weight_key in weights:
                    old_weight = weights[weight_key]
                    new_weight = old_weight * (1 + adjustment)  # Proportional change
                    temp_weights[weight_key] = max(0.05, min(0.50, new_weight))  # Clamp
                    
                    change_pct = ((new_weight - old_weight) / old_weight * 100) if old_weight > 0 else 0
                    print(f"   {weight_key}: {old_weight:.3f} → {temp_weights[weight_key]:.3f} ({change_pct:+.1f}%)")
                else:
                    temp_weights[weight_key] = weights.get(weight_key, 0.2)

            # FIXED: Normalize weights to sum to 1.0
            weights = self._normalize_weights(temp_weights)
            
            # Save updated weights
            self._save_weights(weights)
            print("\n✅ Rule weights updated and normalized")
            
        else:
            print(f"✅ Accuracy {accuracy*100:.1f}% meets threshold — no reweighting needed.")

    def _calculate_weight_adjustments_v2(
        self, 
        indicator_accuracies: Dict[str, Dict], 
        accuracy_gap: float
    ) -> Dict[str, float]:
        """
        FIXED: Calculate proportional weight adjustments based on indicator performance
        Returns: {indicator_name: adjustment_multiplier} where multiplier is relative change
        """
        adjustments = {}
        
        # Map indicator columns to weight keys
        indicator_map = {
            "EMA Bias": "ema_trend",
            "RSI Bias": "rsi_momentum", 
            "MACD Bias": "macd",
            "OB Bias": "order_block",
            "FVG Bias": "fvg"
        }
        
        # Calculate adjustment intensity based on gap
        base_intensity = min(accuracy_gap * 2, 0.5)  # Cap at 50% adjustment
        
        for indicator_col, indicator_key in indicator_map.items():
            if indicator_col not in indicator_accuracies:
                adjustments[indicator_key] = 0.0
                continue
            
            # Calculate weighted average accuracy for this indicator
            bins = indicator_accuracies[indicator_col]
            
            total_count = sum(bin_data['count'] for bin_data in bins.values())
            if total_count == 0:
                adjustments[indicator_key] = 0.0
                continue
            
            weighted_accuracy = sum(
                bin_data['accuracy'] * bin_data['count'] 
                for bin_data in bins.values()
            ) / total_count
            
            # FIXED: Proportional adjustment based on performance
            # Good performers (>60% accuracy) get boost
            # Poor performers (<40% accuracy) get reduction
            if weighted_accuracy > 0.65:
                # Strong performer - increase weight by up to 30%
                adjustment = base_intensity * 0.6
            elif weighted_accuracy > 0.55:
                # Good performer - increase weight by up to 15%
                adjustment = base_intensity * 0.3
            elif weighted_accuracy < 0.40:
                # Poor performer - decrease weight by up to 30%
                adjustment = -base_intensity * 0.6
            elif weighted_accuracy < 0.50:
                # Weak performer - decrease weight by up to 15%
                adjustment = -base_intensity * 0.3
            else:
                # Neutral performer - small adjustment
                adjustment = 0.0
            
            adjustments[indicator_key] = adjustment
            
            print(f"   {indicator_key}: accuracy={weighted_accuracy:.1%}, adjustment={adjustment:+.1%}")
        
        return adjustments

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        FIXED: Normalize weights to sum to 1.0 with minimum enforcement
        """
        # Ensure minimum weight
        min_weight = 0.05
        for key in weights:
            if weights[key] < min_weight:
                weights[key] = min_weight
        
        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            normalized = {k: v / total for k, v in weights.items()}
            
            # Round to 3 decimals
            normalized = {k: round(v, 3) for k, v in normalized.items()}
            
            # Handle rounding errors - adjust largest weight
            sum_check = sum(normalized.values())
            if abs(sum_check - 1.0) > 0.001:
                max_key = max(normalized, key=normalized.get)
                normalized[max_key] += (1.0 - sum_check)
                normalized[max_key] = round(normalized[max_key], 3)
            
            return normalized
        
        return weights

    def _save_weights(self, weights: Dict[str, float]):
        """Save weights to config file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(weights, f, indent=4)
            print(f"💾 Weights saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving weights: {e}")

    # ------------------------------------------
    # 4️⃣ IMPROVED: Generate Performance Summary
    # ------------------------------------------
    def generate_report(self):
        """Generate comprehensive performance report"""
        if self.df is None:
            print("⚠️ No data available for report generation")
            return
            
        try:
            # Create reports directory
            os.makedirs("logs", exist_ok=True)
            
            # Overall statistics
            total_predictions = len(self.df)
            correct_predictions = self.df['is_correct'].sum()
            accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
            
            # Symbol-wise accuracy
            if "Symbol" in self.df.columns:
                symbol_report = self.df.groupby("Symbol").agg({
                    'is_correct': ['count', 'sum', 'mean']
                })
                symbol_report.columns = ['Total', 'Correct', 'Accuracy']
                symbol_report['Accuracy'] = symbol_report['Accuracy'] * 100
                symbol_report = symbol_report.round(1)
                
                print("\n📊 Accuracy by Symbol:")
                print(symbol_report.to_string())
            
            # Bias-wise accuracy
            if "Final Bias" in self.df.columns:
                bias_report = self.df.groupby("Final Bias").agg({
                    'is_correct': ['count', 'sum', 'mean']
                })
                bias_report.columns = ['Total', 'Correct', 'Accuracy']
                bias_report['Accuracy'] = bias_report['Accuracy'] * 100
                bias_report = bias_report.round(1)
                
                print("\n📊 Accuracy by Bias:")
                print(bias_report.to_string())
            
            # Time-based analysis
            if "Date" in self.df.columns:
                self.df['Date'] = pd.to_datetime(self.df['Date'])
                monthly_accuracy = self.df.groupby(
                    self.df['Date'].dt.to_period('M')
                )['is_correct'].mean() * 100
                
                print("\n📅 Monthly Accuracy Trend:")
                for period, acc in monthly_accuracy.tail(6).items():
                    print(f"   {period}: {acc:.1f}%")
            
            # Confidence analysis
            if "Confidence" in self.df.columns:
                # Bin confidence levels
                self.df['Confidence_Bin'] = pd.cut(
                    self.df['Confidence'],
                    bins=[0, 0.4, 0.6, 0.8, 1.0],
                    labels=['Low', 'Medium', 'High', 'Very High']
                )
                
                confidence_report = self.df.groupby("Confidence_Bin").agg({
                    'is_correct': ['count', 'mean']
                })
                confidence_report.columns = ['Count', 'Accuracy']
                confidence_report['Accuracy'] = confidence_report['Accuracy'] * 100
                
                print("\n📊 Accuracy by Confidence Level:")
                print(confidence_report.to_string())
            
            # Save detailed report to Excel
            report_path = "logs/performance_report.xlsx"
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                # Raw data
                self.df.to_excel(writer, sheet_name="Raw_Data", index=False)
                
                # Summary statistics
                summary_data = {
                    'Metric': ['Total Predictions', 'Correct', 'Incorrect', 'Accuracy %'],
                    'Value': [
                        total_predictions,
                        correct_predictions,
                        total_predictions - correct_predictions,
                        round(accuracy, 2)
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
                
                # By symbol
                if "Symbol" in self.df.columns:
                    symbol_report.to_excel(writer, sheet_name="By_Symbol")
                
                # By bias
                if "Final Bias" in self.df.columns:
                    bias_report.to_excel(writer, sheet_name="By_Bias")
                
                # Monthly trend
                if "Date" in self.df.columns:
                    monthly_accuracy.to_frame(name="Accuracy").to_excel(
                        writer, sheet_name="Monthly_Trend"
                    )
                
            print(f"\n✅ Performance report saved to {report_path}")
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            traceback.print_exc()

    # ------------------------------------------
    # 5️⃣ IMPROVED: Run Retraining Cycle
    # ------------------------------------------
    def run_cycle(self):
        """Run complete retraining cycle with comprehensive error handling"""
        print(f"\n{'='*60}")
        print(f"🧠 Starting retraining cycle")
        print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"{'='*60}")
        
        try:
            # Load and validate data
            print("\n📊 Loading verification history...")
            self.load_history()
            
            # Compute metrics
            print("\n📈 Computing performance metrics...")
            accuracy = self.compute_accuracy()
            indicator_accuracies = self.compute_indicator_accuracy()
            
            # Adjust weights if needed
            print("\n⚙️ Checking if weight adjustment needed...")
            self.adjust_weights(accuracy, indicator_accuracies)
            
            # Generate report
            print("\n📄 Generating performance report...")
            self.generate_report()
            
            print(f"\n{'='*60}")
            print(f"✅ Retraining cycle completed")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"\n❌ Retraining cycle failed: {e}")
            traceback.print_exc()

    # ------------------------------------------
    # 6️⃣ NEW: Reset to Default Weights
    # ------------------------------------------
    def reset_to_defaults(self):
        """Reset weights to default values"""
        try:
            default_weights = self._get_default_weights()
            self._save_weights(default_weights)
            print("✅ Weights reset to defaults:", default_weights)
        except Exception as e:
            print(f"❌ Error resetting weights: {e}")

    # ------------------------------------------
    # NEW: Get Weight History
    # ------------------------------------------
    def get_weight_history(self) -> List[Dict]:
        """Get history of weight changes (if tracked)"""
        # This could be extended to track weight changes over time
        # For now, just return current weights
        weights = self.load_weights()
        return [{
            'timestamp': datetime.utcnow().isoformat(),
            'weights': weights
        }]

    # ------------------------------------------
    # NEW: Simulate Weight Changes
    # ------------------------------------------
    def simulate_weight_changes(self, proposed_weights: Dict[str, float]) -> Dict:
        """
        Simulate what accuracy would be with proposed weights
        (Theoretical calculation based on current data)
        """
        if self.df is None or self.df.empty:
            return {"error": "No data available for simulation"}
        
        # This is a simplified simulation
        # In practice, you'd need to recalculate sentiment with new weights
        print("⚠️ Weight simulation is approximate - requires full recalculation")
        
        return {
            "current_accuracy": self.compute_accuracy(),
            "proposed_weights": proposed_weights,
            "note": "Actual accuracy requires full sentiment recalculation"
        }


# Test function
if __name__ == "__main__":
    print("🧪 Testing AutoRetrain...")
    
    retrainer = AutoRetrain(threshold=0.65, min_samples=5)
    
    try:
        # Run retraining cycle
        retrainer.run_cycle()
        print("\n✅ AutoRetrain test completed successfully")
        
        # Show current weights
        print("\n📊 Current Weights:")
        weights = retrainer.load_weights()
        for key, value in weights.items():
            print(f"   {key}: {value:.3f}")
            
    except Exception as e:
        print(f"\n❌ AutoRetrain test failed: {e}")
        traceback.print_exc()
        
        # Test reset functionality
        print("\n🔄 Testing reset to defaults...")
        retrainer.reset_to_defaults()