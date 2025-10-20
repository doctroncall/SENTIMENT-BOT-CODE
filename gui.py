import os
import io
import contextlib
import traceback
from typing import List, Tuple, Optional, Dict
from datetime import datetime

import pandas as pd

# Make Streamlit optional at import-time to avoid hard failures during checks
try:
    import streamlit as st  # type: ignore
    STREAMLIT_AVAILABLE = True
except Exception:
    STREAMLIT_AVAILABLE = False
    class _StreamlitStub:
        def __getattr__(self, _):
            raise RuntimeError(
                "Streamlit is required to run this GUI. Install with: pip install streamlit"
            )
    st = _StreamlitStub()  # type: ignore

# Local imports
from dashboard import Dashboard


def ensure_dashboard() -> Dashboard:
    """Create or fetch a persistent Dashboard instance in session state."""
    if "dashboard" not in st.session_state:
        st.session_state.dashboard = Dashboard()
    return st.session_state.dashboard


def parse_symbols(input_text: str) -> List[str]:
    symbols = [s.strip() for s in input_text.replace("\n", ",").split(",") if s.strip()]
    return symbols


def capture_output(fn, *args, **kwargs) -> Tuple[Optional[object], str, Optional[BaseException]]:
    """Run a function while capturing stdout prints. Returns (result, output_text, error)."""
    buffer = io.StringIO()
    result = None
    err: Optional[BaseException] = None
    with contextlib.redirect_stdout(buffer):
        try:
            result = fn(*args, **kwargs)
        except BaseException as e:
            err = e
            traceback.print_exc()
    return result, buffer.getvalue(), err


def get_mt5_status(dashboard: Dashboard) -> Dict:
    """Get MT5 connection status and details"""
    try:
        is_connected = dashboard.data_manager.is_connected()
        use_mt5 = dashboard.data_manager.use_mt5
        
        status = {
            'connected': is_connected,
            'enabled': use_mt5,
            'login': dashboard.data_manager.mt5_login if use_mt5 else "N/A",
            'server': dashboard.data_manager.mt5_server if use_mt5 else "N/A",
        }
        return status
    except Exception as e:
        return {
            'connected': False,
            'enabled': False,
            'login': "Error",
            'server': str(e),
            'error': True
        }


def render_mt5_connection_card(dashboard: Dashboard) -> None:
    """Render MT5 connection status card with controls"""
    mt5_status = get_mt5_status(dashboard)
    
    # Connection Status Header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if mt5_status.get('error'):
            st.error("🔴 **MT5 Status:** Error")
        elif not mt5_status['enabled']:
            st.warning("⚠️ **MT5 Status:** Disabled")
        elif mt5_status['connected']:
            st.success("🟢 **MT5 Status:** Connected")
        else:
            st.warning("🟡 **MT5 Status:** Disconnected")
    
    with col2:
        if mt5_status['enabled'] and not mt5_status['connected']:
            if st.button("🔌 Connect MT5", use_container_width=True, type="primary"):
                with st.spinner("Connecting to MT5..."):
                    success = dashboard.data_manager.connect()
                if success:
                    st.success("✅ Connected!")
                    st.rerun()
                else:
                    st.error("❌ Connection failed")
    
    with col3:
        if mt5_status['connected']:
            if st.button("🔌 Disconnect", use_container_width=True):
                dashboard.data_manager.disconnect()
                st.info("Disconnected from MT5")
                st.rerun()
    
    # Connection Details
    if mt5_status['enabled']:
        with st.expander("📋 MT5 Connection Details", expanded=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.text(f"Login: {mt5_status['login']}")
                st.text(f"Server: {mt5_status['server']}")
            with col_b:
                st.text(f"Enabled: {'Yes' if mt5_status['enabled'] else 'No'}")
                st.text(f"Status: {'Connected' if mt5_status['connected'] else 'Disconnected'}")


def render_system_metrics(dashboard: Dashboard) -> None:
    """Render system metrics in a card layout"""
    st.subheader("📊 System Metrics")
    
    # Get metrics
    excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total predictions
        if os.path.exists(excel_file):
            try:
                df = pd.read_excel(excel_file)
                total_predictions = len(df)
            except:
                total_predictions = 0
        else:
            total_predictions = 0
        
        st.metric("Total Predictions", total_predictions)
    
    with col2:
        # Accuracy
        if os.path.exists(excel_file):
            try:
                df = pd.read_excel(excel_file)
                if "Verified" in df.columns:
                    verified_mask = df["Verified"].isin(["✅ True", "❌ False"])
                    verified_df = df[verified_mask]
                    if not verified_df.empty:
                        correct = (verified_df["Verified"] == "✅ True").sum()
                        accuracy = (correct / len(verified_df)) * 100
                    else:
                        accuracy = 0
                else:
                    accuracy = 0
            except:
                accuracy = 0
        else:
            accuracy = 0
        
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    with col3:
        # Tracked symbols
        num_symbols = len(dashboard.symbols)
        st.metric("Tracked Symbols", num_symbols)
    
    with col4:
        # MT5 Status
        mt5_status = get_mt5_status(dashboard)
        status_text = "🟢 Online" if mt5_status['connected'] else "🔴 Offline"
        st.metric("MT5 Connection", status_text)


def render_latest_log_table(excel_file: str) -> None:
    """Render latest sentiment log with improved styling"""
    st.subheader("📈 Recent Predictions")
    
    if not os.path.exists(excel_file):
        st.info("📝 No sentiment log file found yet. Run an analysis first.")
        return
    
    try:
        df = pd.read_excel(excel_file)
        if df.empty:
            st.info("📝 Sentiment log is empty.")
            return
        
        # Show last 20 entries by date
        display_cols = [
            col for col in ["Date", "Symbol", "Final Bias", "Confidence", "Verified", "Weighted Score"]
            if col in df.columns
        ]
        
        # Display with better formatting
        st.dataframe(
            df.tail(20)[display_cols],
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
    except Exception as e:
        st.error(f"❌ Could not read {excel_file}: {e}")


def render_reports_section(report_dir: str) -> None:
    """Render reports section with improved UI"""
    st.subheader("📄 Analysis Reports")
    
    if not os.path.isdir(report_dir):
        st.info("📁 No reports directory yet. Reports will appear here after running analysis.")
        return
    
    files = sorted(
        [f for f in os.listdir(report_dir) if os.path.isfile(os.path.join(report_dir, f))],
        reverse=True,
    )
    
    if not files:
        st.info("📁 No reports generated yet. Run an analysis to generate reports.")
        return
    
    # Display report selector and download
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selection = st.selectbox("Select a report to view", files, index=0, label_visibility="collapsed")
    
    with col2:
        if selection:
            path = os.path.join(report_dir, selection)
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
                mime = "application/pdf" if selection.lower().endswith(".pdf") else "text/plain"
                st.download_button(
                    label="⬇️ Download",
                    data=data,
                    file_name=selection,
                    mime=mime,
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"❌ Failed to load report: {e}")
    
    # Preview for text reports
    if selection and selection.lower().endswith(".txt"):
        try:
            path = os.path.join(report_dir, selection)
            with open(path, "rb") as fh:
                data = fh.read()
            text = data.decode("utf-8", errors="replace")
            
            with st.expander("👁️ Preview Report", expanded=True):
                st.text_area("", value=text, height=400, label_visibility="collapsed")
        except Exception as e:
            st.error(f"❌ Preview failed: {e}")


def render_health_check(dashboard: Dashboard, show_logs: bool) -> None:
    """Render health check section"""
    st.subheader("🏥 System Health Check")
    
    if st.button("🔍 Run Health Check", use_container_width=True, type="secondary"):
        with st.spinner("Running health check..."):
            ok, out, err = capture_output(dashboard.health_check)
        
        # Display results
        col1, col2 = st.columns([1, 3])
        with col1:
            if err:
                st.error("❌ Check Failed")
            elif ok:
                st.success("✅ All Systems OK")
            else:
                st.warning("⚠️ Issues Detected")
        
        if show_logs and out:
            with st.expander("📋 Detailed Results", expanded=True):
                st.text(out)


def main() -> None:
    if not STREAMLIT_AVAILABLE:
        raise RuntimeError(
            "Streamlit is required to run this GUI. Install with: pip install streamlit\n"
            "Or run via: streamlit run gui.py"
        )

    # Page configuration
    st.set_page_config(
        page_title="Trading Bot Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="🤖"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .section-header {
            background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
            padding: 0.5rem;
            border-radius: 5px;
            color: white;
            margin-bottom: 1rem;
        }
        .stButton>button {
            border-radius: 5px;
            font-weight: 500;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #1f77b4;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<div class="main-header">🤖 Trading Bot Dashboard</div>', unsafe_allow_html=True)
    st.markdown("*Automated trading sentiment analysis with MT5 integration*")
    
    dashboard = ensure_dashboard()
    
    # ============================================================
    # SIDEBAR - Configuration & Settings
    # ============================================================
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Trading+Bot", use_container_width=True)
        st.markdown("---")
        
        st.header("⚙️ Configuration")
        
        # Symbol configuration
        with st.expander("📊 Trading Symbols", expanded=True):
            default_symbols = ", ".join(dashboard.symbols) if hasattr(dashboard, "symbols") else "GBPUSD, XAUUSD"
            symbols_text = st.text_area(
                "Symbols (comma or newline separated)",
                value=default_symbols,
                height=100,
                help="Enter trading symbols separated by commas or newlines"
            )
            
            if st.button("✅ Apply Symbols", use_container_width=True, type="primary"):
                symbols = parse_symbols(symbols_text)
                if symbols:
                    dashboard.symbols = symbols
                    st.success(f"✅ Applied {len(symbols)} symbols")
                    st.rerun()
                else:
                    st.warning("⚠️ No valid symbols provided")
        
        # Settings
        with st.expander("🔧 Settings", expanded=False):
            allow_synth = st.toggle(
                "Allow synthetic fallback",
                value=True,
                help="Use synthetic data when both MT5 and Yahoo Finance fail"
            )
            
            show_logs = st.toggle(
                "Show operation logs",
                value=True,
                help="Display detailed logs for operations"
            )
            
            auto_refresh = st.toggle(
                "Auto-refresh data",
                value=False,
                help="Automatically refresh data display"
            )
            
            # Apply settings
            if allow_synth:
                os.environ["ALLOW_SYNTHETIC_DATA"] = "1"
            else:
                os.environ["ALLOW_SYNTHETIC_DATA"] = "0"
        
        st.markdown("---")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.rerun()
        
        if st.button("🧹 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache cleared")
        
        st.markdown("---")
        st.caption(f"🕒 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        st.caption("💡 Tip: Use `streamlit run gui.py` to launch")
    
    # ============================================================
    # MAIN CONTENT AREA
    # ============================================================
    
    # MT5 Connection Status (always visible at top)
    with st.container():
        render_mt5_connection_card(dashboard)
    
    st.markdown("---")
    
    # System Metrics Dashboard
    with st.container():
        render_system_metrics(dashboard)
    
    st.markdown("---")
    
    # ============================================================
    # TABBED INTERFACE
    # ============================================================
    tab_home, tab_analyze, tab_verify, tab_reports, tab_health = st.tabs([
        "🏠 Home",
        "📊 Analysis",
        "✅ Verification",
        "📄 Reports",
        "🏥 Health"
    ])
    
    # -------------------- HOME TAB --------------------
    with tab_home:
        st.header("Welcome to Trading Bot Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📖 Quick Start Guide")
            st.markdown("""
            1. **Check MT5 Connection** - Ensure MT5 is connected (see status above)
            2. **Configure Symbols** - Set your trading symbols in the sidebar
            3. **Run Analysis** - Go to the Analysis tab to analyze markets
            4. **View Reports** - Check generated reports in the Reports tab
            5. **Verify Predictions** - Use the Verification tab to check accuracy
            """)
            
            st.info("💡 **Pro Tip:** Enable auto-refresh in settings for real-time updates")
        
        with col2:
            st.subheader("📈 Current Status")
            render_latest_log_table(getattr(dashboard, "excel_file", "sentiment_log.xlsx"))
    
    # -------------------- ANALYSIS TAB --------------------
    with tab_analyze:
        st.header("📊 Market Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Full Analysis")
            st.markdown("Run complete analysis for all configured symbols")
            
            if st.button("▶️ Run Full Analysis", use_container_width=True, type="primary"):
                with st.spinner("🔄 Running full analysis... This may take a few minutes"):
                    result, out, err = capture_output(dashboard.run_full_cycle)
                
                if err:
                    st.error(f"❌ Analysis failed: {err}")
                else:
                    st.success("✅ Analysis completed successfully!")
                    st.balloons()
                
                if show_logs and out:
                    with st.expander("📋 Analysis Logs", expanded=False):
                        st.text(out)
        
        with col2:
            st.subheader("🔍 Single Symbol Analysis")
            st.markdown("Analyze a specific symbol on demand")
            
            manual_symbol = st.text_input(
                "Enter symbol",
                placeholder="e.g., GBPUSD, EURUSD, XAUUSD",
                label_visibility="collapsed"
            )
            
            if st.button("▶️ Run Single Analysis", use_container_width=True, type="secondary"):
                if manual_symbol.strip():
                    with st.spinner(f"🔄 Analyzing {manual_symbol.strip()}..."):
                        result, out, err = capture_output(dashboard.run_manual_analysis, manual_symbol.strip())
                    
                    if err:
                        st.error(f"❌ Analysis failed: {err}")
                    else:
                        st.success(f"✅ Analysis completed for {manual_symbol.strip()}")
                    
                    if show_logs and out:
                        with st.expander("📋 Analysis Logs", expanded=False):
                            st.text(out)
                else:
                    st.warning("⚠️ Please enter a symbol")
        
        st.markdown("---")
        
        # Quick status display
        st.subheader("📊 Recent Analysis Results")
        if st.button("🔄 Refresh Status", use_container_width=False):
            with st.spinner("Loading status..."):
                _, out, err = capture_output(dashboard.show_status)
            if show_logs and out:
                with st.expander("Status Output", expanded=True):
                    st.text(out)
    
    # -------------------- VERIFICATION TAB --------------------
    with tab_verify:
        st.header("✅ Verification & Retraining")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Run Verification")
            st.markdown("Verify prediction accuracy against actual market movements")
            
            if st.button("▶️ Verify Predictions", use_container_width=True, type="primary"):
                with st.spinner("🔄 Verifying predictions..."):
                    _, out, err = capture_output(dashboard.run_verification)
                
                if err:
                    st.error(f"❌ Verification failed: {err}")
                else:
                    st.success("✅ Verification completed!")
                
                if show_logs and out:
                    with st.expander("📋 Verification Logs", expanded=False):
                        st.text(out)
        
        with col2:
            st.subheader("🧠 Run Retraining")
            st.markdown("Retrain sentiment engine based on verified results")
            
            if st.button("▶️ Run Retraining", use_container_width=True, type="secondary"):
                with st.spinner("🔄 Running retraining... This may take a while"):
                    _, out, err = capture_output(dashboard.run_retrain)
                
                if err:
                    st.error(f"❌ Retraining failed: {err}")
                else:
                    st.success("✅ Retraining completed!")
                
                if show_logs and out:
                    with st.expander("📋 Retraining Logs", expanded=False):
                        st.text(out)
        
        st.markdown("---")
        
        # Display verification results
        st.subheader("📊 Verification Results")
        excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
        
        if os.path.exists(excel_file):
            try:
                df = pd.read_excel(excel_file)
                
                if "Verified" in df.columns:
                    verified_mask = df["Verified"].isin(["✅ True", "❌ False"])
                    verified_df = df[verified_mask]
                    
                    if not verified_df.empty:
                        col_a, col_b, col_c = st.columns(3)
                        
                        correct = (verified_df["Verified"] == "✅ True").sum()
                        total = len(verified_df)
                        accuracy = (correct / total) * 100
                        
                        with col_a:
                            st.metric("Total Verified", total)
                        with col_b:
                            st.metric("Correct Predictions", correct)
                        with col_c:
                            st.metric("Accuracy", f"{accuracy:.1f}%")
                        
                        # Show by symbol
                        if "Symbol" in verified_df.columns:
                            st.subheader("📈 Accuracy by Symbol")
                            
                            symbol_stats = []
                            for symbol in verified_df["Symbol"].unique():
                                symbol_df = verified_df[verified_df["Symbol"] == symbol]
                                symbol_correct = (symbol_df["Verified"] == "✅ True").sum()
                                symbol_total = len(symbol_df)
                                symbol_acc = (symbol_correct / symbol_total * 100) if symbol_total > 0 else 0
                                
                                symbol_stats.append({
                                    "Symbol": symbol,
                                    "Total": symbol_total,
                                    "Correct": symbol_correct,
                                    "Accuracy": f"{symbol_acc:.1f}%"
                                })
                            
                            st.dataframe(pd.DataFrame(symbol_stats), use_container_width=True, hide_index=True)
                    else:
                        st.info("📝 No verified predictions yet")
                else:
                    st.info("📝 No verification data available")
            except Exception as e:
                st.error(f"❌ Error loading verification data: {e}")
        else:
            st.info("📝 No sentiment log file found")
    
    # -------------------- REPORTS TAB --------------------
    with tab_reports:
        st.header("📄 Analysis Reports")
        render_reports_section("reports")
    
    # -------------------- HEALTH TAB --------------------
    with tab_health:
        st.header("🏥 System Health")
        render_health_check(dashboard, show_logs)
        
        st.markdown("---")
        
        # System information
        st.subheader("ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Dashboard Info**")
            st.text(f"Tracked Symbols: {', '.join(dashboard.symbols)}")
            st.text(f"Excel File: {getattr(dashboard, 'excel_file', 'N/A')}")
            st.text(f"Reports Directory: reports/")
        
        with col2:
            st.markdown("**🔌 Data Manager Info**")
            mt5_status = get_mt5_status(dashboard)
            st.text(f"MT5 Enabled: {mt5_status['enabled']}")
            st.text(f"MT5 Connected: {mt5_status['connected']}")
            if mt5_status['enabled']:
                st.text(f"MT5 Server: {mt5_status['server']}")


if __name__ == "__main__":
    main()
