# report_generator.py - FIXED VERSION
import os
import datetime
import pandas as pd
import traceback
from typing import Dict, Optional

# Try to import reportlab components (optional dependency)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not available - PDF reports will be disabled")


class ReportGenerator:
    def __init__(self, report_dir="reports", excel_file="sentiment_log.xlsx"):
        self.report_dir = report_dir
        self.excel_file = excel_file
        os.makedirs(report_dir, exist_ok=True)
        
        # Create logs directory if needed
        os.makedirs("logs", exist_ok=True)
        
        self.pdf_enabled = REPORTLAB_AVAILABLE

    # ------------------------------------------
    # 1️⃣ IMPROVED: Generate Daily PDF Report
    # ------------------------------------------
    def generate_pdf(self, symbol: str, sentiment_data: dict) -> Optional[str]:
        """
        FIXED: Generate PDF report with better error handling and formatting
        """
        if not self.pdf_enabled:
            print("⚠️ PDF generation skipped - ReportLab not installed")
            return self._create_text_report(symbol, sentiment_data)
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"{symbol}_{today}_sentiment_report.pdf"
        path = os.path.join(self.report_dir, filename)

        try:
            doc = SimpleDocTemplate(path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # FIXED: Custom styles for better formatting
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=12
            )

            # Title
            story.append(Paragraph("TRADING SENTIMENT ANALYSIS REPORT", title_style))
            story.append(Spacer(1, 0.2 * inch))
            
            # FIXED: Header Information with better formatting
            header_data = [
                ["Symbol", symbol],
                ["Date", today],
                ["Final Bias", f"<b>{sentiment_data['final_bias'].upper()}</b>"],
                ["Confidence", f"{sentiment_data['final_confidence']*100:.1f}%"],
                ["Weighted Score", f"{sentiment_data.get('final_score', 0):+.3f}"],
                ["Analysis Time", sentiment_data.get('analysis_time', datetime.datetime.now().strftime("%H:%M UTC"))]
            ]
            
            header_table = Table(header_data, colWidths=[2*inch, 3.5*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),  # Bold bias
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(header_table)
            story.append(Spacer(1, 0.3 * inch))

            # FIXED: Bias Score Breakdown with better visuals
            story.append(Paragraph("<b>INDICATOR SCORE BREAKDOWN</b>", heading_style))
            
            if 'score_breakdown' in sentiment_data or 'scores' in sentiment_data:
                scores = sentiment_data.get('scores', sentiment_data.get('score_breakdown', {}))
                
                score_data = [["Indicator", "Score", "Signal"]]
                
                indicator_names = {
                    'ema_trend': 'EMA Trend',
                    'rsi_momentum': 'RSI Momentum',
                    'macd': 'MACD',
                    'order_block': 'Order Block',
                    'fvg': 'Fair Value Gap'
                }
                
                for key, name in indicator_names.items():
                    score = scores.get(key, sentiment_data.get(f'{key}_bias', 0))
                    
                    # Visual signal indicator
                    if score > 0.5:
                        signal = "🟢🟢 Strong Bullish"
                    elif score > 0:
                        signal = "🟢 Bullish"
                    elif score < -0.5:
                        signal = "🔴🔴 Strong Bearish"
                    elif score < 0:
                        signal = "🔴 Bearish"
                    else:
                        signal = "⚪ Neutral"
                    
                    score_data.append([name, f"{score:+.3f}", signal])
                
                score_table = Table(score_data, colWidths=[2*inch, 1*inch, 2.5*inch])
                score_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(score_table)
                story.append(Spacer(1, 0.2 * inch))

            # FIXED: Timeframe Analysis with better organization
            story.append(Paragraph("<b>TIMEFRAME ANALYSIS</b>", heading_style))
            
            timeframe_details = sentiment_data.get('timeframe_details', {})
            if timeframe_details:
                for tf, data in timeframe_details.items():
                    bias = data.get('bias', 'Unknown')
                    confidence = data.get('confidence', 0)
                    
                    # Color-coded bias
                    if bias.lower() == 'bullish':
                        bias_color = colors.green
                        bias_icon = "📈"
                    elif bias.lower() == 'bearish':
                        bias_color = colors.red
                        bias_icon = "📉"
                    else:
                        bias_color = colors.grey
                        bias_icon = "↔️"
                    
                    story.append(Paragraph(
                        f"<b>{tf} Timeframe:</b> {bias_icon} "
                        f"<font color='{bias_color}'>{bias.upper()}</font> "
                        f"(Confidence: {confidence*100:.0f}%)", 
                        styles['Normal']
                    ))
                    
                    # Reasons
                    reasons = data.get('reasons', [])
                    if reasons:
                        for reason in reasons[:5]:  # Limit to 5 main reasons
                            story.append(Paragraph(f"  • {reason}", styles['Normal']))
                    
                    story.append(Spacer(1, 0.1 * inch))
            else:
                story.append(Paragraph("No timeframe details available", styles['Normal']))

            # FIXED: Market Structure Summary
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("<b>MARKET STRUCTURE SUMMARY</b>", heading_style))
            
            structure_summary = sentiment_data.get('structure_summary', {})
            if structure_summary:
                for key, value in structure_summary.items():
                    story.append(Paragraph(f"• <b>{key}:</b> {value}", styles['Normal']))
            else:
                story.append(Paragraph("No structure analysis available", styles['Normal']))

            # FIXED: Trading Recommendations with risk assessment
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("<b>TRADING RECOMMENDATIONS</b>", heading_style))
            
            bias = sentiment_data['final_bias'].lower()
            confidence = sentiment_data['final_confidence']
            
            # Confidence level assessment
            if confidence > 0.75:
                confidence_level = "HIGH CONFIDENCE"
                confidence_color = colors.HexColor('#27ae60')
                risk_level = "Moderate Risk"
            elif confidence > 0.5:
                confidence_level = "MEDIUM CONFIDENCE"
                confidence_color = colors.HexColor('#f39c12')
                risk_level = "Elevated Risk"
            elif confidence > 0.3:
                confidence_level = "LOW CONFIDENCE"
                confidence_color = colors.HexColor('#e74c3c')
                risk_level = "High Risk"
            else:
                confidence_level = "VERY LOW CONFIDENCE"
                confidence_color = colors.HexColor('#c0392b')
                risk_level = "Very High Risk"
            
            story.append(Paragraph(
                f"<b>Signal Strength:</b> <font color='{confidence_color}'>{confidence_level}</font> "
                f"({confidence:.0%})",
                styles['Normal']
            ))
            story.append(Paragraph(f"<b>Risk Assessment:</b> {risk_level}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
            
            # Specific recommendations
            if bias == 'bullish' and confidence > 0.4:
                story.append(Paragraph("• <b>Direction:</b> Consider long positions", styles['Normal']))
                story.append(Paragraph("• <b>Entry:</b> Look for pullbacks to support levels", styles['Normal']))
                story.append(Paragraph("• <b>Stop Loss:</b> Below recent swing low", styles['Normal']))
                story.append(Paragraph("• <b>Risk Management:</b> Use proper position sizing", styles['Normal']))
            elif bias == 'bearish' and confidence > 0.4:
                story.append(Paragraph("• <b>Direction:</b> Consider short positions", styles['Normal']))
                story.append(Paragraph("• <b>Entry:</b> Look for rallies to resistance levels", styles['Normal']))
                story.append(Paragraph("• <b>Stop Loss:</b> Above recent swing high", styles['Normal']))
                story.append(Paragraph("• <b>Risk Management:</b> Use proper position sizing", styles['Normal']))
            else:
                story.append(Paragraph("• <b>Recommendation:</b> Wait for clearer market direction", styles['Normal']))
                story.append(Paragraph("• <b>Action:</b> Consider reduced position sizes or staying flat", styles['Normal']))
                story.append(Paragraph("• <b>Strategy:</b> Monitor for improving signal clarity", styles['Normal']))

            # Footer / Disclaimer
            story.append(Spacer(1, 0.4 * inch))
            story.append(Paragraph(
                "<i>This report is generated automatically based on technical analysis. "
                "Next verification scheduled in 24 hours.</i>",
                styles['Italic']
            ))
            story.append(Paragraph(
                "<i><b>Risk Warning:</b> Trading involves substantial risk of loss. "
                "Past performance is not indicative of future results. "
                "Always use proper risk management.</i>",
                styles['Italic']
            ))

            # Build PDF
            doc.build(story)
            print(f"✅ PDF Report saved: {path}")
            return path
            
        except Exception as e:
            print(f"❌ Error generating PDF report: {e}")
            traceback.print_exc()
            # Create a text report as fallback
            return self._create_text_report(symbol, sentiment_data)

    def _create_text_report(self, symbol: str, sentiment_data: dict) -> str:
        """
        FIXED: Create enhanced text report as fallback when PDF fails
        """
        today = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"{symbol}_{today}_report.txt"
        path = os.path.join(self.report_dir, filename)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("TRADING SENTIMENT ANALYSIS REPORT\n")
                f.write("="*60 + "\n\n")
                
                # Header
                f.write(f"Symbol: {symbol}\n")
                f.write(f"Date: {today}\n")
                f.write(f"Final Bias: {sentiment_data['final_bias'].upper()}\n")
                f.write(f"Confidence: {sentiment_data['final_confidence']*100:.1f}%\n")
                f.write(f"Weighted Score: {sentiment_data.get('final_score', 0):+.3f}\n")
                f.write("\n" + "-"*60 + "\n\n")
                
                # Indicator Scores
                f.write("INDICATOR BREAKDOWN:\n")
                scores = sentiment_data.get('scores', {})
                for indicator, score in scores.items():
                    signal = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"
                    f.write(f"  {indicator.replace('_', ' ').title():20}: {score:+.3f} ({signal})\n")
                
                f.write("\n" + "-"*60 + "\n\n")
                
                # Timeframe Analysis
                f.write("TIMEFRAME ANALYSIS:\n")
                for tf, data in sentiment_data.get('timeframe_details', {}).items():
                    f.write(f"\n  {tf}:\n")
                    f.write(f"    Bias: {data.get('bias', 'Unknown')}\n")
                    f.write(f"    Confidence: {data.get('confidence', 0)*100:.0f}%\n")
                    
                    reasons = data.get('reasons', [])
                    if reasons:
                        f.write("    Reasons:\n")
                        for reason in reasons[:3]:
                            f.write(f"      - {reason}\n")
                
                f.write("\n" + "-"*60 + "\n\n")
                
                # Recommendations
                f.write("RECOMMENDATIONS:\n")
                confidence = sentiment_data['final_confidence']
                bias = sentiment_data['final_bias'].lower()
                
                if confidence > 0.5:
                    if bias == 'bullish':
                        f.write("  - Consider long positions with proper risk management\n")
                        f.write("  - Look for entry on pullbacks\n")
                    elif bias == 'bearish':
                        f.write("  - Consider short positions with proper risk management\n")
                        f.write("  - Look for entry on rallies\n")
                else:
                    f.write("  - Low confidence - wait for clearer signals\n")
                    f.write("  - Consider staying flat or using reduced position sizes\n")
                
                f.write("\n" + "="*60 + "\n")
                f.write("Report generated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC") + "\n")
                f.write("Risk Warning: Trading involves substantial risk of loss.\n")
                f.write("="*60 + "\n")
            
            print(f"✅ Text Report saved: {path}")
            return path
            
        except Exception as e:
            print(f"❌ Error creating text report: {e}")
            return ""

    # ------------------------------------------
    # 2️⃣ IMPROVED: Update Excel Log
    # ------------------------------------------
    def update_excel_log(self, symbol: str, sentiment_data: dict):
        """FIXED: Update Excel log with comprehensive error handling"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        try:
            # Create new record
            record = {
                "Date": today,
                "Symbol": symbol,
                "Final Bias": sentiment_data['final_bias'],
                "Confidence": round(sentiment_data['final_confidence'], 4),
                "Weighted Score": round(sentiment_data.get('final_score', 0), 4),
                "EMA_Bias": sentiment_data.get('ema_bias', 0),
                "RSI_Bias": sentiment_data.get('rsi_bias', 0),
                "MACD_Bias": sentiment_data.get('macd_bias', 0),
                "OB_Bias": sentiment_data.get('ob_bias', 0),
                "FVG_Bias": sentiment_data.get('fvg_bias', 0),
                "Reason_Summary": self._create_reason_summary(sentiment_data),
                "Verified": "Pending",
                "Report_Generated": "Yes",
                "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "Trend_Context": sentiment_data.get('structure_summary', {}).get('Trend Context', 'unknown')
            }

            df_new = pd.DataFrame([record])

            # If Excel exists, append or update
            if os.path.exists(self.excel_file):
                try:
                    df_old = pd.read_excel(self.excel_file)
                    
                    # FIXED: Avoid duplicates for same date/symbol
                    mask = ~((df_old['Date'] == today) & (df_old['Symbol'] == symbol))
                    df_combined = pd.concat([df_old[mask], df_new], ignore_index=True)
                    
                except Exception as e:
                    print(f"⚠️ Error reading existing Excel file, creating new: {e}")
                    df_combined = df_new
            else:
                df_combined = df_new

            # Save to Excel
            df_combined.to_excel(self.excel_file, index=False, engine='openpyxl')
            print(f"✅ Excel Log updated: {self.excel_file}")
            
        except Exception as e:
            print(f"❌ Error updating Excel log: {e}")
            traceback.print_exc()
            # Try to save as CSV as fallback
            self._save_csv_fallback(record)

    def _create_reason_summary(self, sentiment_data: dict) -> str:
        """Create a concise reason summary"""
        reasons = []
        
        # Extract reasons from timeframe details
        for tf, data in sentiment_data.get('timeframe_details', {}).items():
            tf_reasons = data.get('reasons', [])
            if tf_reasons:
                reasons.append(f"{tf}: {tf_reasons[0]}")
        
        # If no timeframe reasons, use indicator summaries
        if not reasons:
            scores = sentiment_data.get('scores', {})
            for indicator, score in scores.items():
                if abs(score) > 0.5:
                    direction = "bullish" if score > 0 else "bearish"
                    reasons.append(f"{indicator} {direction}")
        
        return "; ".join(reasons[:3]) if reasons else "Mixed signals"

    def _save_csv_fallback(self, record: dict):
        """Save to CSV as fallback when Excel fails"""
        try:
            csv_file = self.excel_file.replace('.xlsx', '.csv')
            df = pd.DataFrame([record])
            
            # Append if exists, otherwise create new
            if os.path.exists(csv_file):
                df.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_file, mode='w', header=True, index=False)
            
            print(f"✅ CSV fallback saved: {csv_file}")
        except Exception as e:
            print(f"❌ CSV fallback also failed: {e}")

    # ------------------------------------------
    # 3️⃣ IMPROVED: Generate Both Reports Together
    # ------------------------------------------
    def generate_reports(self, symbol: str, sentiment_data: dict) -> Optional[str]:
        """
        FIXED: Generate both PDF and Excel reports with comprehensive error handling
        """
        print(f"\n📄 Generating reports for {symbol}...")
        
        try:
            # Enhance sentiment data with additional information
            enhanced_data = self._enhance_sentiment_data(symbol, sentiment_data)
            
            # Generate PDF report (or text fallback)
            pdf_path = self.generate_pdf(symbol, enhanced_data)
            
            # Update Excel log
            self.update_excel_log(symbol, enhanced_data)
            
            return pdf_path
            
        except Exception as e:
            print(f"❌ Error generating reports for {symbol}: {e}")
            traceback.print_exc()
            return None

    def _enhance_sentiment_data(self, symbol: str, sentiment_data: dict) -> dict:
        """Enhance sentiment data with additional analysis information"""
        enhanced = sentiment_data.copy()
        
        # Add current market time
        enhanced['analysis_time'] = datetime.datetime.now().strftime("%H:%M UTC")
        
        # Add score breakdown if not present but individual scores are
        if 'score_breakdown' not in enhanced and 'scores' in enhanced:
            enhanced['score_breakdown'] = {}
            
            weights = {
                'ema_trend': 0.25,
                'rsi_momentum': 0.20,
                'macd': 0.15,
                'order_block': 0.25,
                'fvg': 0.15
            }
            
            for indicator, weight in weights.items():
                score = enhanced['scores'].get(indicator, 0)
                enhanced['score_breakdown'][indicator] = {
                    'score': score,
                    'weight': weight,
                    'contribution': score * weight
                }
        
        return enhanced


# Test function
if __name__ == "__main__":
    # Test the report generator
    print("🧪 Testing Report Generator...")
    
    sample_data = {
        'final_bias': 'bullish',
        'final_confidence': 0.75,
        'final_score': 0.42,
        'ema_bias': 1,
        'rsi_bias': 0.6,
        'macd_bias': 0.8,
        'ob_bias': 1,
        'fvg_bias': 0.5,
        'scores': {
            'ema_trend': 1,
            'rsi_momentum': 0.6,
            'macd': 0.8,
            'order_block': 1,
            'fvg': 0.5
        },
        'timeframe_details': {
            'D1': {
                'bias': 'bullish',
                'confidence': 0.8,
                'reasons': [
                    'Price above EMA 200',
                    'RSI showing bullish momentum',
                    'Bullish order block detected',
                    'MACD bullish crossover'
                ]
            },
            'H4': {
                'bias': 'bullish', 
                'confidence': 0.7,
                'reasons': [
                    'Break of structure to upside',
                    'Bullish fair value gap present'
                ]
            }
        },
        'structure_summary': {
            'Order Block Bias': '+1.00',
            'FVG Bias': '+0.50',
            'Trend Context': 'uptrend',
            'Analysis Time': '14:30'
        }
    }
    
    generator = ReportGenerator()
    
    try:
        result = generator.generate_reports("GBPUSD", sample_data)
        if result:
            print(f"\n✅ Test completed successfully!")
            print(f"   Report saved: {result}")
        else:
            print("\n⚠️ Report generation returned None")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()