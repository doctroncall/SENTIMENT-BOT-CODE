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
from status_monitor import get_monitor, EventType


def ensure_dashboard() -> Dashboard:
    """Create or fetch a persistent Dashboard instance in session state."""
    if "dashboard" not in st.session_state:
        st.session_state.dashboard = Dashboard()
    return st.session_state.dashboard


def render_status_monitor() -> None:
    """Render real-time status monitor with event log and statistics"""
    st.header("📊 Real-Time Application Status")
    
    monitor = get_monitor()
    
    # Add controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("**Live monitoring of all application activities**")
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, key="status_auto_refresh")
    with col3:
        if st.button("🔄 Refresh Now", width='stretch'):
            st.rerun()
    with col4:
        if st.button("🧹 Clear Log", width='stretch'):
            monitor.clear()
            st.success("Status log cleared!")
            st.rerun()
    
    st.markdown("---")
    
    # Statistics Dashboard
    st.subheader("📈 Activity Statistics")
    stats = monitor.get_stats()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Events", stats['total_events'])
    with col2:
        st.metric("Successes", stats['successes'], delta_color="normal")
    with col3:
        st.metric("Failures", stats['failures'], delta_color="inverse")
    with col4:
        st.metric("Warnings", stats['warnings'], delta_color="off")
    with col5:
        st.metric("Data Fetches", stats['data_fetches'])
    with col6:
        st.metric("Analyses", stats['analyses'])
    
    st.markdown("---")
    
    # Event filtering
    st.subheader("🔍 Event Log")
    
    col_filter, col_count = st.columns([3, 1])
    
    with col_filter:
        filter_option = st.selectbox(
            "Filter by type",
            ["All Events", "Success", "Error", "Warning", "Data Fetch", "Analysis", "Connection", "Info", "Cache"],
            index=0
        )
    
    with col_count:
        event_count = st.number_input("Show last N events", min_value=10, max_value=500, value=100, step=10)
    
    # Get filtered events
    filter_map = {
        "All Events": None,
        "Success": EventType.SUCCESS,
        "Error": EventType.ERROR,
        "Warning": EventType.WARNING,
        "Data Fetch": EventType.DATA_FETCH,
        "Analysis": EventType.ANALYSIS,
        "Connection": EventType.CONNECTION,
        "Info": EventType.INFO,
        "Cache": EventType.CACHE
    }
    
    event_type_filter = filter_map.get(filter_option)
    events = monitor.get_filtered_events(event_type_filter, count=event_count)
    
    # Display events in a formatted table
    if events:
        st.markdown(f"**Showing {len(events)} most recent events** (newest first)")
        
        # Create DataFrame for better display
        import pandas as pd
        df_events = pd.DataFrame(events)
        
        # Style the dataframe
        st.dataframe(
            df_events,
            column_config={
                "timestamp": st.column_config.TextColumn("Time", width="small"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "message": st.column_config.TextColumn("Message", width="large"),
                "details": st.column_config.TextColumn("Details", width="medium")
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
        
        # Detailed event view
        with st.expander("📋 Detailed Event Log (Text Format)", expanded=False):
            event_text = "\n".join([
                f"[{e['timestamp']}] {e['type']} {e['message']}" + 
                (f" - {e['details']}" if e['details'] else "")
                for e in events
            ])
            st.text_area("", value=event_text, height=400, label_visibility="collapsed")
    else:
        st.info("📝 No events logged yet. Events will appear here as the application runs.")
    
    # Auto-refresh section
    st.markdown("---")
    
    if auto_refresh:
        st.caption(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')} | Auto-refreshing every second...")
        
        # Use a placeholder and auto-refresh with JavaScript
        # This is a more efficient approach than using time.sleep + st.rerun
        import time
        time.sleep(1)
        st.rerun()
    else:
        st.caption(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')} | Auto-refresh disabled. Click 'Refresh Now' to update manually.")


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
            if st.button("🔌 Connect MT5", width='stretch', type="primary"):
                with st.spinner("Connecting to MT5..."):
                    try:
                        success = dashboard.data_manager.connect()
                    except Exception as e:
                        st.error(f"❌ Connection error: {str(e)}")
                        success = False
                if success:
                    st.success("✅ Connected!")
                    st.rerun()
                else:
                    st.error("❌ Connection failed - Check troubleshooting below")
    
    with col3:
        if mt5_status['connected']:
            if st.button("🔌 Disconnect", width='stretch'):
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
        
        # Troubleshooting section - only show if not connected
        if not mt5_status['connected']:
            with st.expander("🔧 Troubleshooting - Connection Issues", expanded=False):
                st.markdown("""
                **If connection gets stuck or fails:**
                
                1. **Check MT5 Terminal is Running**
                   - Open MetaTrader 5 desktop application
                   - Make sure you're logged in
                   
                2. **Verify Credentials**
                   - Login: {login}
                   - Server: {server}
                   - Check these match your MT5 terminal
                   
                3. **Restart MT5 Terminal**
                   - Close MetaTrader 5 completely
                   - Wait 5 seconds
                   - Reopen and login
                   - Try connecting again
                   
                4. **Check Terminal Path**
                   - Default: `C:\\Program Files\\MetaTrader 5\\terminal64.exe`
                   - Set MT5_PATH environment variable if different
                   
                5. **Enable Algo Trading**
                   - In MT5: Tools → Options → Expert Advisors
                   - Check "Allow automated trading"
                   - Check "Allow DLL imports"
                """.format(login=mt5_status['login'], server=mt5_status['server']))
                
                st.info("💡 **Tip:** Most connection issues are fixed by restarting MT5 terminal")


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
            width='stretch',
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
                    width='stretch',
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
    
    if st.button("🔍 Run Health Check", width='stretch', type="secondary"):
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
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Trading+Bot", width='stretch')
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
            
            if st.button("✅ Apply Symbols", width='stretch', type="primary"):
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
        if st.button("🔄 Refresh Dashboard", width='stretch'):
            st.rerun()
        
        if st.button("🧹 Clear Cache", width='stretch'):
            st.cache_data.clear()
            # Also clear status monitor
            from status_monitor import get_monitor, log_cache
            get_monitor().clear()
            log_cache("Cache and status log cleared")
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
    tab_home, tab_status, tab_analyze, tab_verify, tab_reports, tab_health, tab_help = st.tabs([
        "🏠 Home",
        "📊 Status Monitor",
        "📈 Analysis",
        "✅ Verification",
        "📄 Reports",
        "🏥 Health",
        "❓ Help"
    ])
    
    # -------------------- HOME TAB --------------------
    with tab_home:
        st.header("🏠 Welcome to Trading Sentiment Analysis Dashboard")
        
        # System status overview
        st.subheader("📊 System Status Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # MT5 status
            mt5_status = get_mt5_status(dashboard)
            if mt5_status['connected']:
                st.success("🟢 **MT5 Connected**")
            elif mt5_status['enabled']:
                st.warning("🟡 **MT5 Disconnected**")
            else:
                st.info("⚪ **MT5 Disabled**")
        
        with col2:
            # Data availability
            excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
            if os.path.exists(excel_file):
                try:
                    df = pd.read_excel(excel_file)
                    st.success(f"📊 **{len(df)} Predictions**")
                except:
                    st.warning("📊 **Log Exists**")
            else:
                st.info("📊 **No Data Yet**")
        
        with col3:
            # Reports available
            if os.path.exists("reports"):
                try:
                    report_count = len([f for f in os.listdir("reports") if os.path.isfile(os.path.join("reports", f))])
                    st.success(f"📄 **{report_count} Reports**")
                except:
                    st.info("📄 **Reports Ready**")
            else:
                st.info("📄 **No Reports**")
        
        with col4:
            # Verification status
            if os.path.exists(excel_file):
                try:
                    df = pd.read_excel(excel_file)
                    if "Verified" in df.columns:
                        verified_count = df["Verified"].isin(["✅ True", "❌ False"]).sum()
                        if verified_count > 0:
                            st.success(f"✅ **{verified_count} Verified**")
                        else:
                            st.info("✅ **Not Verified**")
                    else:
                        st.info("✅ **Not Verified**")
                except:
                    st.info("✅ **Not Verified**")
            else:
                st.info("✅ **Not Verified**")
        
        st.markdown("---")
        
        # Two-column layout
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("🚀 Quick Start Guide")
            
            st.markdown("""
            ### For First-Time Users:
            
            **Step 1: Check MT5 Connection** 🔌
            - Ensure MT5 terminal is running and logged in
            - Check connection status above
            - If disconnected, click "Connect MT5" at the top
            
            **Step 2: Configure Symbols** ⚙️
            - Use the sidebar to set your trading symbols
            - Enter symbols like: `GBPUSD, EURUSD, XAUUSD`
            - Click "Apply Symbols" to save
            
            **Step 3: Run Your First Analysis** 📊
            - Go to the **Analysis** tab
            - Choose "Automatic" mode for all symbols
            - Click "Run Analysis" and wait for completion
            
            **Step 4: View Results** 📈
            - Check the **Reports** tab for detailed analysis
            - Reports are generated in TXT and PDF formats
            - Download or preview reports directly
            
            **Step 5: Verify & Improve** ✅
            - After 1+ days, go to **Verification** tab
            - Click "Verify All Predictions"
            - Review accuracy and run retraining if needed
            
            ---
            
            ### Daily Workflow:
            
            1. **Morning**: Run analysis (Analysis tab)
            2. **Review**: Check reports (Reports tab)
            3. **Evening**: Verify previous predictions (Verification tab)
            4. **Monitor**: Use Status Monitor tab for live updates
            
            ---
            
            💡 **Pro Tips:**
            - Use the **Status Monitor** tab to see real-time activity
            - Run **Health Check** (Health tab) if you encounter issues
            - Configure **Auto-refresh** in sidebar for live monitoring
            - The system learns and improves through verification
            """)
        
        with col_right:
            st.subheader("📈 Recent Activity")
            
            # Latest predictions
            excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
            
            if os.path.exists(excel_file):
                try:
                    df = pd.read_excel(excel_file)
                    
                    if not df.empty:
                        # Show summary stats
                        st.markdown("### 📊 Performance Summary")
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.metric("Total Predictions", len(df))
                            
                            # Symbols analyzed
                            if "Symbol" in df.columns:
                                unique_symbols = df["Symbol"].nunique()
                                st.metric("Symbols Tracked", unique_symbols)
                        
                        with col_b:
                            # Accuracy if available
                            if "Verified" in df.columns:
                                verified_mask = df["Verified"].isin(["✅ True", "❌ False"])
                                verified_df = df[verified_mask]
                                
                                if not verified_df.empty:
                                    correct = (verified_df["Verified"] == "✅ True").sum()
                                    total = len(verified_df)
                                    accuracy = (correct / total) * 100
                                    st.metric("Accuracy", f"{accuracy:.1f}%")
                                    st.metric("Verified Count", total)
                        
                        st.markdown("---")
                        
                        # Latest predictions table
                        st.markdown("### 📋 Latest Predictions")
                        
                        display_cols = ["Date", "Symbol", "Final Bias", "Confidence"]
                        if "Verified" in df.columns:
                            display_cols.append("Verified")
                        
                        latest_df = df[display_cols].tail(10).sort_values("Date", ascending=False)
                        
                        st.dataframe(
                            latest_df,
                            width='stretch',
                            hide_index=True,
                            height=300
                        )
                        
                        # Quick action buttons
                        st.markdown("---")
                        st.markdown("### ⚡ Quick Actions")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("📊 Run New Analysis", type="primary", use_container_width=True, key="home_new_analysis"):
                                st.switch_page("pages/Analysis")  # This won't work in single page, but we can use session state
                                # Alternative: just rerun and user clicks on Analysis tab
                                st.info("👉 Go to the **Analysis** tab to run a new analysis")
                        
                        with col_btn2:
                            if st.button("✅ Verify Predictions", type="secondary", use_container_width=True, key="home_verify"):
                                st.info("👉 Go to the **Verification** tab to verify predictions")
                    
                    else:
                        st.info("📝 **No predictions yet**")
                        st.markdown("""
                        **Get started:**
                        1. Go to the **Analysis** tab
                        2. Click "Run Analysis"
                        3. Results will appear here!
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Error loading data: {e}")
            
            else:
                st.info("📝 **No sentiment log found**")
                st.markdown("""
                **Welcome! Let's get started:**
                
                1. Check that MT5 is connected (see status above)
                2. Configure your symbols in the sidebar
                3. Go to the **Analysis** tab
                4. Run your first analysis!
                
                Your predictions and results will appear here once you start analyzing.
                """)
                
                if st.button("🚀 Get Started - Run First Analysis", type="primary", use_container_width=True):
                    st.info("👉 Go to the **Analysis** tab and click 'Run Analysis'")
        
        st.markdown("---")
        
        # Feature highlights
        st.subheader("✨ Key Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🤖 Automated Analysis**
            - Multi-timeframe analysis
            - Technical indicators (EMA, RSI, MACD)
            - Market structure detection
            - Order blocks & FVG analysis
            """)
        
        with col2:
            st.markdown("""
            **✅ Verification System**
            - Automatic accuracy tracking
            - Per-symbol performance
            - Bias-type breakdown
            - Historical accuracy trends
            """)
        
        with col3:
            st.markdown("""
            **🧠 Adaptive Learning**
            - Auto-retraining based on performance
            - Rule weight optimization
            - Continuous improvement
            - Confidence calibration
            """)
    
    # -------------------- STATUS MONITOR TAB --------------------
    with tab_status:
        render_status_monitor()
    
    # -------------------- ANALYSIS TAB --------------------
    with tab_analyze:
        st.header("📊 Market Analysis")
        
        # Analysis Mode Selection
        st.subheader("📋 Analysis Mode")
        analysis_mode = st.radio(
            "Choose analysis mode:",
            ["🤖 Automatic (All Symbols)", "🎯 Manual (Single Symbol)"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if "Automatic" in analysis_mode:
            # Automatic Analysis Section
            st.subheader("🤖 Automatic Analysis")
            st.markdown("Run complete analysis for all configured symbols")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📊 **Symbols to analyze:** {', '.join(dashboard.symbols)}")
            
            with col2:
                if st.button("▶️ Run Analysis", width='stretch', type="primary", key="auto_analysis"):
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
            
            with col3:
                if st.button("📊 View Results", width='stretch', type="secondary", key="view_auto_results"):
                    st.rerun()
            
            # Show latest results table
            st.markdown("---")
            st.subheader("📈 Latest Analysis Results")
            render_latest_log_table(getattr(dashboard, "excel_file", "sentiment_log.xlsx"))
            
        else:
            # Manual Analysis Section
            st.subheader("🎯 Manual Single Symbol Analysis")
            st.markdown("Analyze a specific symbol on demand")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                manual_symbol = st.text_input(
                    "Enter symbol to analyze",
                    placeholder="e.g., GBPUSD, EURUSD, XAUUSD",
                    key="manual_symbol_input"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                if st.button("▶️ Analyze", width='stretch', type="primary", key="manual_analysis"):
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
            
            # Quick reference
            st.markdown("---")
            st.subheader("💡 Symbol Examples")
            st.markdown("""
            **Forex Pairs:** EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF  
            **Commodities:** XAUUSD (Gold), XAGUSD (Silver), USOIL (Oil)  
            **Indices:** US30, SPX500, NAS100, UK100  
            **Crypto:** BTCUSD, ETHUSD (if available on your broker)
            """)
        
        st.markdown("---")
        
        # Status Display
        st.subheader("📊 System Status")
        col_a, col_b = st.columns([1, 3])
        
        with col_a:
            if st.button("🔄 Refresh Status", width='stretch', type="secondary"):
                st.rerun()
        
        with col_b:
            excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
            if os.path.exists(excel_file):
                try:
                    df = pd.read_excel(excel_file)
                    st.success(f"✅ {len(df)} total predictions logged")
                except:
                    st.info("📝 Sentiment log exists but couldn't be read")
            else:
                st.info("📝 No sentiment log yet - run your first analysis!")
    
    # -------------------- VERIFICATION TAB --------------------
    with tab_verify:
        st.header("✅ Verification & Model Retraining")
        
        # Workflow explanation
        st.info("💡 **Workflow:** Verify predictions → Review accuracy → Retrain if needed → Improve performance")
        
        st.markdown("---")
        
        # Action buttons
        st.subheader("🔧 Verification Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Verify All Predictions", width='stretch', type="primary", key="verify_all"):
                with st.spinner("🔄 Verifying predictions against actual market data..."):
                    _, out, err = capture_output(dashboard.run_verification)
                
                if err:
                    st.error(f"❌ Verification failed: {err}")
                    if show_logs:
                        with st.expander("Error Details", expanded=True):
                            st.text(str(err))
                else:
                    st.success("✅ Verification completed!")
                    st.rerun()  # Refresh to show new results
                
                if show_logs and out:
                    with st.expander("📋 Verification Logs", expanded=False):
                        st.text(out)
        
        with col2:
            if st.button("🧠 Run Adaptive Retraining", width='stretch', type="secondary", key="retrain"):
                with st.spinner("🔄 Running adaptive retraining... This may take a while"):
                    _, out, err = capture_output(dashboard.run_retrain)
                
                if err:
                    st.error(f"❌ Retraining failed: {err}")
                else:
                    st.success("✅ Retraining completed!")
                
                if show_logs and out:
                    with st.expander("📋 Retraining Logs", expanded=False):
                        st.text(out)
        
        with col3:
            if st.button("🔄 Refresh Results", width='stretch', key="refresh_verify"):
                st.rerun()
        
        st.markdown("---")
        
        # Display verification results
        st.subheader("📊 Verification Results & Performance Metrics")
        excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
        
        if os.path.exists(excel_file):
            try:
                df = pd.read_excel(excel_file)
                
                # Check for pending verifications
                if "Verified" in df.columns:
                    pending_mask = df["Verified"].isin(["Pending", "pending", "PENDING", None, ""])
                    pending_count = pending_mask.sum()
                    
                    if pending_count > 0:
                        st.warning(f"⏳ **{pending_count} predictions pending verification** - Click 'Verify All Predictions' to check them")
                    
                    verified_mask = df["Verified"].isin(["✅ True", "❌ False"])
                    verified_df = df[verified_mask]
                    
                    if not verified_df.empty:
                        # Overall accuracy metrics
                        col_a, col_b, col_c, col_d = st.columns(4)
                        
                        correct = (verified_df["Verified"] == "✅ True").sum()
                        incorrect = (verified_df["Verified"] == "❌ False").sum()
                        total = len(verified_df)
                        accuracy = (correct / total) * 100 if total > 0 else 0
                        
                        with col_a:
                            st.metric("Total Verified", total, delta=f"+{pending_count} pending" if pending_count > 0 else None)
                        with col_b:
                            st.metric("Correct ✅", correct, delta=f"{(correct/total*100):.1f}%" if total > 0 else "0%")
                        with col_c:
                            st.metric("Incorrect ❌", incorrect, delta=f"{(incorrect/total*100):.1f}%" if total > 0 else "0%", delta_color="inverse")
                        with col_d:
                            # Color code accuracy
                            if accuracy >= 70:
                                st.metric("Overall Accuracy", f"{accuracy:.1f}%", delta="Good", delta_color="normal")
                            elif accuracy >= 50:
                                st.metric("Overall Accuracy", f"{accuracy:.1f}%", delta="Fair", delta_color="off")
                            else:
                                st.metric("Overall Accuracy", f"{accuracy:.1f}%", delta="Needs Improvement", delta_color="inverse")
                        
                        st.markdown("---")
                        
                        # Detailed breakdowns
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            # Accuracy by symbol
                            if "Symbol" in verified_df.columns and len(verified_df["Symbol"].unique()) > 1:
                                st.subheader("📈 Accuracy by Symbol")
                                
                                symbol_stats = []
                                for symbol in sorted(verified_df["Symbol"].unique()):
                                    symbol_df = verified_df[verified_df["Symbol"] == symbol]
                                    symbol_correct = (symbol_df["Verified"] == "✅ True").sum()
                                    symbol_total = len(symbol_df)
                                    symbol_acc = (symbol_correct / symbol_total * 100) if symbol_total > 0 else 0
                                    
                                    symbol_stats.append({
                                        "Symbol": symbol,
                                        "Verified": symbol_total,
                                        "Correct": symbol_correct,
                                        "Incorrect": symbol_total - symbol_correct,
                                        "Accuracy": f"{symbol_acc:.1f}%"
                                    })
                                
                                st.dataframe(
                                    pd.DataFrame(symbol_stats),
                                    width='stretch',
                                    hide_index=True,
                                    height=300
                                )
                        
                        with col_right:
                            # Accuracy by bias type
                            if "Final Bias" in verified_df.columns:
                                st.subheader("🎯 Accuracy by Bias Type")
                                
                                bias_stats = []
                                for bias in ["Bullish", "Bearish", "Neutral"]:
                                    bias_df = verified_df[verified_df["Final Bias"].str.lower() == bias.lower()]
                                    if not bias_df.empty:
                                        bias_correct = (bias_df["Verified"] == "✅ True").sum()
                                        bias_total = len(bias_df)
                                        bias_acc = (bias_correct / bias_total * 100) if bias_total > 0 else 0
                                        
                                        bias_stats.append({
                                            "Bias Type": bias,
                                            "Count": bias_total,
                                            "Correct": bias_correct,
                                            "Accuracy": f"{bias_acc:.1f}%"
                                        })
                                
                                if bias_stats:
                                    st.dataframe(
                                        pd.DataFrame(bias_stats),
                                        width='stretch',
                                        hide_index=True,
                                        height=150
                                    )
                        
                        st.markdown("---")
                        
                        # Recent verified predictions
                        st.subheader("📋 Recent Verified Predictions")
                        
                        display_cols = ["Date", "Symbol", "Final Bias", "Confidence", "Verified"]
                        
                        # Add optional columns if they exist
                        optional_cols = ["Actual Bias", "Movement_Pct", "Close Movement"]
                        for col in optional_cols:
                            if col in verified_df.columns:
                                display_cols.append(col)
                        
                        recent_verified = verified_df[display_cols].tail(20).sort_values("Date", ascending=False)
                        
                        st.dataframe(
                            recent_verified,
                            width='stretch',
                            hide_index=True,
                            height=400
                        )
                        
                    else:
                        st.info("📝 **No verified predictions yet**")
                        st.markdown("""
                        **To get started:**
                        1. Run an analysis in the Analysis tab
                        2. Wait at least 1 day for market movement
                        3. Click 'Verify All Predictions' to check accuracy
                        """)
                else:
                    st.info("📝 No verification column in sentiment log")
                    
            except Exception as e:
                st.error(f"❌ Error loading verification data: {e}")
                if show_logs:
                    with st.expander("Error Details"):
                        st.text(str(e))
        else:
            st.info("📝 **No sentiment log file found**")
            st.markdown("Run your first analysis in the Analysis tab to generate predictions!")
    
    # -------------------- REPORTS TAB --------------------
    with tab_reports:
        st.header("📄 Analysis Reports & Downloads")
        
        # Report controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**View and download generated analysis reports**")
        
        with col2:
            if st.button("🔄 Refresh List", width='stretch', key="refresh_reports"):
                st.rerun()
        
        with col3:
            if st.button("📂 Open Folder", width='stretch', key="open_reports_folder"):
                import platform
                import subprocess
                try:
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', 'reports'])
                    elif platform.system() == 'Windows':
                        subprocess.run(['explorer', 'reports'])
                    else:  # Linux
                        subprocess.run(['xdg-open', 'reports'])
                    st.success("✅ Opened reports folder")
                except Exception as e:
                    st.error(f"❌ Could not open folder: {e}")
        
        st.markdown("---")
        
        # Enhanced reports section
        report_dir = "reports"
        
        if not os.path.isdir(report_dir):
            st.warning("📁 **No reports directory found**")
            st.markdown("""
            Reports will be generated automatically when you run an analysis.
            
            **To generate reports:**
            1. Go to the Analysis tab
            2. Run a full analysis or single symbol analysis
            3. Reports will appear here once generated
            """)
            
            # Offer to create directory
            if st.button("📁 Create Reports Directory", type="secondary"):
                try:
                    os.makedirs(report_dir, exist_ok=True)
                    st.success(f"✅ Created {report_dir} directory")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Could not create directory: {e}")
        else:
            files = sorted(
                [f for f in os.listdir(report_dir) if os.path.isfile(os.path.join(report_dir, f))],
                key=lambda x: os.path.getmtime(os.path.join(report_dir, x)),
                reverse=True,
            )
            
            if not files:
                st.info("📁 **Reports directory is empty**")
                st.markdown("""
                No reports have been generated yet.
                
                **To generate reports:**
                - Go to the Analysis tab and run an analysis
                - Reports will be automatically generated for each symbol
                - Both text (.txt) and PDF (.pdf) formats are created
                """)
            else:
                # Show report count and types
                txt_files = [f for f in files if f.endswith('.txt')]
                pdf_files = [f for f in files if f.endswith('.pdf')]
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Reports", len(files))
                with col_b:
                    st.metric("Text Reports", len(txt_files))
                with col_c:
                    st.metric("PDF Reports", len(pdf_files))
                
                st.markdown("---")
                
                # File type filter
                file_type_filter = st.selectbox(
                    "Filter by type:",
                    ["All Files", "Text Reports (.txt)", "PDF Reports (.pdf)"],
                    key="report_type_filter"
                )
                
                # Apply filter
                if "Text" in file_type_filter:
                    files = txt_files
                elif "PDF" in file_type_filter:
                    files = pdf_files
                
                # Symbol filter if there are multiple symbols
                symbols_in_reports = set()
                for f in files:
                    # Extract symbol from filename (format: SYMBOL_YYYYMMDD_HHMMSS.ext)
                    parts = f.split('_')
                    if len(parts) >= 1:
                        symbols_in_reports.add(parts[0])
                
                if len(symbols_in_reports) > 1:
                    symbol_filter = st.selectbox(
                        "Filter by symbol:",
                        ["All Symbols"] + sorted(list(symbols_in_reports)),
                        key="report_symbol_filter"
                    )
                    
                    if symbol_filter != "All Symbols":
                        files = [f for f in files if f.startswith(symbol_filter)]
                
                st.markdown("---")
                
                # Display reports list with selection
                st.subheader(f"📋 Available Reports ({len(files)})")
                
                if files:
                    # Create a nice selection interface
                    selected_report = st.selectbox(
                        "Select a report to view",
                        files,
                        index=0,
                        format_func=lambda x: f"{x} ({os.path.getsize(os.path.join(report_dir, x)) / 1024:.1f} KB)",
                        key="selected_report"
                    )
                    
                    if selected_report:
                        report_path = os.path.join(report_dir, selected_report)
                        
                        # Report info
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.text(f"File: {selected_report}")
                        with col2:
                            file_size = os.path.getsize(report_path) / 1024
                            st.text(f"Size: {file_size:.1f} KB")
                        with col3:
                            mod_time = datetime.fromtimestamp(os.path.getmtime(report_path))
                            st.text(f"Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Download button
                        try:
                            with open(report_path, "rb") as fh:
                                data = fh.read()
                            
                            mime = "application/pdf" if selected_report.lower().endswith(".pdf") else "text/plain"
                            
                            st.download_button(
                                label="⬇️ Download Report",
                                data=data,
                                file_name=selected_report,
                                mime=mime,
                                type="primary",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to load report: {e}")
                        
                        # Preview for text reports
                        if selected_report.lower().endswith(".txt"):
                            st.markdown("---")
                            st.subheader("👁️ Report Preview")
                            
                            try:
                                with open(report_path, "r", encoding="utf-8", errors="replace") as fh:
                                    content = fh.read()
                                
                                # Show in expandable text area
                                st.text_area(
                                    "Report Content",
                                    value=content,
                                    height=500,
                                    label_visibility="collapsed"
                                )
                            except Exception as e:
                                st.error(f"❌ Preview failed: {e}")
                        
                        elif selected_report.lower().endswith(".pdf"):
                            st.info("💡 **PDF files cannot be previewed in the browser.** Click 'Download Report' to view the PDF.")
                else:
                    st.info("No reports match the selected filters")
        
        # Additional help section
        st.markdown("---")
        with st.expander("ℹ️ About Reports", expanded=False):
            st.markdown("""
            ### Report Types
            
            **Text Reports (.txt)**
            - Human-readable format
            - Contains detailed analysis breakdown
            - Easy to view and share
            - Includes all technical indicators and signals
            
            **PDF Reports (.pdf)**
            - Professional formatted reports
            - Suitable for printing and formal documentation
            - Contains the same information as text reports
            
            ### Report Contents
            
            Each report includes:
            - Symbol and timeframe analyzed
            - Final sentiment bias (Bullish/Bearish/Neutral)
            - Confidence level
            - Technical indicator breakdowns:
              - EMA trend analysis
              - RSI momentum
              - MACD signals
              - Order block detection
              - Fair value gap analysis
            - Detailed reasoning for the bias
            - Analysis timestamp
            
            ### Report Naming
            
            Reports are named: `SYMBOL_YYYYMMDD_HHMMSS.ext`
            - **SYMBOL**: The trading pair/symbol
            - **YYYYMMDD**: Date of analysis
            - **HHMMSS**: Time of analysis
            - **ext**: File extension (.txt or .pdf)
            """)
    
    # -------------------- HEALTH TAB --------------------
    with tab_health:
        st.header("🏥 System Health & Diagnostics")
        
        # Health Check Controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Run comprehensive system health checks**")
        
        with col2:
            run_health = st.button("🔍 Run Health Check", width='stretch', type="primary", key="health_check")
        
        with col3:
            if st.button("🔄 Refresh", width='stretch', key="health_refresh"):
                st.rerun()
        
        st.markdown("---")
        
        # Run health check if button clicked
        if run_health or 'health_check_run' not in st.session_state:
            with st.spinner("Running health check..."):
                ok, out, err = capture_output(dashboard.health_check)
            
            st.session_state.health_check_run = True
            st.session_state.health_output = out
            st.session_state.health_error = err
            st.session_state.health_ok = ok
        
        # Display health check results
        if 'health_check_run' in st.session_state:
            if st.session_state.health_error:
                st.error("❌ Health Check Failed")
                with st.expander("Error Details", expanded=True):
                    st.text(str(st.session_state.health_error))
            elif st.session_state.health_ok:
                st.success("✅ All Systems Operational")
            else:
                st.warning("⚠️ Some Systems Need Attention")
            
            if show_logs and st.session_state.health_output:
                with st.expander("📋 Detailed Health Check Results", expanded=True):
                    st.text(st.session_state.health_output)
        
        st.markdown("---")
        
        # Component Status Dashboard
        st.subheader("🔧 Component Status")
        
        # Create status indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Core Components**")
            
            # Dashboard
            dash_ok = dashboard is not None
            st.markdown(f"{'✅' if dash_ok else '❌'} Dashboard")
            
            # Data Manager
            dm_ok = hasattr(dashboard, 'data_manager') and dashboard.data_manager is not None
            st.markdown(f"{'✅' if dm_ok else '❌'} Data Manager")
            
            # Sentiment Engine
            se_ok = hasattr(dashboard, 'sentiment_engine') and dashboard.sentiment_engine is not None
            st.markdown(f"{'✅' if se_ok else '❌'} Sentiment Engine")
        
        with col2:
            st.markdown("**🔌 Connections**")
            
            # MT5 Connection
            mt5_status = get_mt5_status(dashboard)
            mt5_ok = mt5_status['connected']
            st.markdown(f"{'✅' if mt5_ok else '❌'} MT5 Connection")
            
            # Excel Log
            excel_ok = os.path.exists(getattr(dashboard, 'excel_file', 'sentiment_log.xlsx'))
            st.markdown(f"{'✅' if excel_ok else '⚠️'} Excel Log File")
            
            # Config Directory
            config_ok = os.path.exists('config')
            st.markdown(f"{'✅' if config_ok else '⚠️'} Config Directory")
        
        with col3:
            st.markdown("**📄 Modules**")
            
            # Verifier
            verifier_ok = hasattr(dashboard, 'verifier') and dashboard.verifier is not None
            st.markdown(f"{'✅' if verifier_ok else '❌'} Verifier")
            
            # Retrainer
            retrain_ok = hasattr(dashboard, 'retrainer') and dashboard.retrainer is not None
            st.markdown(f"{'✅' if retrain_ok else '❌'} Auto Retrain")
            
            # Report Generator
            report_ok = hasattr(dashboard, 'report_generator') and dashboard.report_generator is not None
            st.markdown(f"{'✅' if report_ok else '❌'} Report Generator")
        
        st.markdown("---")
        
        # System Information
        st.subheader("ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Dashboard Configuration**")
            st.text(f"Tracked Symbols: {', '.join(dashboard.symbols)}")
            st.text(f"Symbol Count: {len(dashboard.symbols)}")
            st.text(f"Excel File: {getattr(dashboard, 'excel_file', 'N/A')}")
            st.text(f"Reports Directory: reports/")
            
            # Check if reports directory exists
            if os.path.exists('reports'):
                try:
                    report_count = len([f for f in os.listdir('reports') if os.path.isfile(os.path.join('reports', f))])
                    st.text(f"Generated Reports: {report_count}")
                except:
                    st.text(f"Generated Reports: Unknown")
        
        with col2:
            st.markdown("**🔌 MT5 Configuration**")
            mt5_status = get_mt5_status(dashboard)
            st.text(f"MT5 Enabled: {'Yes' if mt5_status['enabled'] else 'No'}")
            st.text(f"MT5 Connected: {'Yes' if mt5_status['connected'] else 'No'}")
            if mt5_status['enabled']:
                st.text(f"MT5 Login: {mt5_status['login']}")
                st.text(f"MT5 Server: {mt5_status['server']}")
            
            # Prediction stats
            excel_file = getattr(dashboard, 'excel_file', 'sentiment_log.xlsx')
            if os.path.exists(excel_file):
                try:
                    df = pd.read_excel(excel_file)
                    st.text(f"Total Predictions: {len(df)}")
                    
                    if "Verified" in df.columns:
                        verified_count = df["Verified"].isin(["✅ True", "❌ False"]).sum()
                        st.text(f"Verified Predictions: {verified_count}")
                except:
                    st.text(f"Total Predictions: Unknown")
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("⚡ Quick Diagnostic Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔌 Test MT5 Connection", width='stretch', type="secondary"):
                with st.spinner("Testing MT5 connection..."):
                    if mt5_status['enabled']:
                        try:
                            if dashboard.data_manager.is_connected():
                                st.success("✅ MT5 already connected")
                            else:
                                connected = dashboard.data_manager.connect()
                                if connected:
                                    st.success("✅ MT5 connection successful")
                                else:
                                    st.error("❌ MT5 connection failed")
                        except Exception as e:
                            st.error(f"❌ Connection error: {str(e)}")
                    else:
                        st.warning("⚠️ MT5 is not enabled")
        
        with col2:
            if st.button("📊 Check Data Access", width='stretch', type="secondary"):
                with st.spinner("Testing data access..."):
                    try:
                        test_symbol = dashboard.symbols[0] if dashboard.symbols else "GBPUSD"
                        df = dashboard.data_manager.fetch_ohlcv_for_timeframe(test_symbol, "D1", lookback_days=5)
                        if df is not None and not df.empty:
                            st.success(f"✅ Successfully fetched {len(df)} bars for {test_symbol}")
                        else:
                            st.error(f"❌ No data retrieved for {test_symbol}")
                    except Exception as e:
                        st.error(f"❌ Data access error: {str(e)}")
        
        with col3:
            if st.button("📄 Check File Permissions", width='stretch', type="secondary"):
                checks = []
                
                # Check Excel file
                excel_file = getattr(dashboard, 'excel_file', 'sentiment_log.xlsx')
                if os.path.exists(excel_file):
                    checks.append(("Excel log readable", os.access(excel_file, os.R_OK)))
                    checks.append(("Excel log writable", os.access(excel_file, os.W_OK)))
                
                # Check reports directory
                if os.path.exists('reports'):
                    checks.append(("Reports dir readable", os.access('reports', os.R_OK)))
                    checks.append(("Reports dir writable", os.access('reports', os.W_OK)))
                
                # Check config directory
                if os.path.exists('config'):
                    checks.append(("Config dir readable", os.access('config', os.R_OK)))
                    checks.append(("Config dir writable", os.access('config', os.W_OK)))
                
                all_ok = all(check[1] for check in checks)
                
                if all_ok:
                    st.success("✅ All file permissions OK")
                else:
                    st.warning("⚠️ Some permission issues detected")
                
                with st.expander("Permission Details"):
                    for check_name, check_ok in checks:
                        st.text(f"{'✅' if check_ok else '❌'} {check_name}")


    # -------------------- HELP TAB --------------------
    with tab_help:
        st.header("❓ Help & Documentation")
        
        # Search/filter help topics
        help_topic = st.selectbox(
            "Select a help topic:",
            [
                "🏠 Getting Started",
                "📊 Running Analysis",
                "✅ Verification Process",
                "📄 Understanding Reports",
                "🔧 Troubleshooting",
                "🤖 About the System",
                "⚙️ Configuration Guide",
                "🔌 MT5 Connection Issues"
            ]
        )
        
        st.markdown("---")
        
        if "Getting Started" in help_topic:
            st.markdown("""
            # 🏠 Getting Started
            
            ## Initial Setup
            
            ### 1. Install Requirements
            Make sure you have all dependencies installed:
            ```bash
            pip install -r requirements.txt
            ```
            
            ### 2. MetaTrader 5 Setup
            - Install MetaTrader 5 terminal
            - Create/login to your trading account
            - Enable automated trading:
              - Tools → Options → Expert Advisors
              - Check "Allow automated trading"
              - Check "Allow DLL imports"
            
            ### 3. Configure Environment Variables (Optional)
            Set these environment variables for automatic MT5 connection:
            - `MT5_LOGIN`: Your MT5 account number
            - `MT5_PASSWORD`: Your MT5 password
            - `MT5_SERVER`: Your broker's server name
            - `MT5_PATH`: Path to MT5 terminal (if not default)
            
            ### 4. Launch the Dashboard
            ```bash
            streamlit run gui.py
            ```
            
            ## First Steps
            
            1. **Check MT5 Connection**
               - Look at the MT5 status card at the top
               - If disconnected, click "Connect MT5"
               - Verify your credentials are correct
            
            2. **Configure Symbols**
               - Open the sidebar (⚙️ Configuration)
               - Enter your desired symbols in "Trading Symbols"
               - Format: `GBPUSD, EURUSD, XAUUSD` (comma-separated)
               - Click "Apply Symbols"
            
            3. **Run Your First Analysis**
               - Go to **Analysis** tab
               - Select "Automatic" mode
               - Click "Run Analysis"
               - Wait for completion (may take 2-5 minutes)
            
            4. **View Results**
               - Check **Reports** tab for detailed analysis
               - Download PDF or text reports
               - Review sentiment predictions
            
            5. **Verify & Improve** (after 1+ days)
               - Go to **Verification** tab
               - Click "Verify All Predictions"
               - Review accuracy
               - Run retraining if accuracy < 70%
            """)
        
        elif "Running Analysis" in help_topic:
            st.markdown("""
            # 📊 Running Analysis
            
            ## Analysis Modes
            
            ### Automatic Mode (Recommended for Daily Analysis)
            - Analyzes all configured symbols
            - Uses multiple timeframes (D1, H4, H1)
            - Generates comprehensive reports
            - Saves predictions to Excel log
            
            **When to use:** Daily market analysis, portfolio-wide sentiment
            
            ### Manual Mode (For Single Symbols)
            - Analyzes one specific symbol
            - Useful for on-demand analysis
            - Quick sentiment check
            - Same accuracy as automatic mode
            
            **When to use:** Checking a specific trade idea, symbol-specific analysis
            
            ## What Gets Analyzed
            
            ### Technical Indicators
            1. **EMA 200** - Long-term trend direction
            2. **RSI (14)** - Momentum and overbought/oversold
            3. **MACD (12, 26, 9)** - Trend strength and reversals
            
            ### Market Structure
            1. **Order Blocks (OB)** - Institutional buying/selling zones
            2. **Fair Value Gaps (FVG)** - Price imbalances
            3. **Higher Highs/Higher Lows** - Trend structure
            
            ### Output
            - **Final Bias**: Bullish, Bearish, or Neutral
            - **Confidence**: 0-100% confidence in the prediction
            - **Weighted Score**: -100 to +100 composite score
            - **Detailed Reports**: TXT and PDF formats
            
            ## Understanding Results
            
            ### Bias Types
            - **Bullish** 🟢: Expect upward price movement
            - **Bearish** 🔴: Expect downward price movement
            - **Neutral** ⚪: No clear directional bias
            
            ### Confidence Levels
            - **80-100%**: Very High - Strong agreement across indicators
            - **60-79%**: High - Good indicator alignment
            - **40-59%**: Moderate - Mixed signals
            - **0-39%**: Low - Weak or conflicting signals
            
            ### Weighted Score
            - **+50 to +100**: Strong bullish
            - **+20 to +49**: Moderate bullish
            - **-20 to +20**: Neutral zone
            - **-49 to -20**: Moderate bearish
            - **-100 to -50**: Strong bearish
            """)
        
        elif "Verification Process" in help_topic:
            st.markdown("""
            # ✅ Verification Process
            
            ## How Verification Works
            
            ### 1. Prediction Storage
            - When you run analysis, predictions are saved with:
              - Date and time
              - Symbol
              - Predicted bias (Bullish/Bearish/Neutral)
              - Confidence level
              - Status: "Pending"
            
            ### 2. Market Movement Check
            - After 1+ days, verification compares:
              - **Prediction day close price**
              - **Next day close price**
              - Calculates actual movement percentage
            
            ### 3. Accuracy Determination
            - **Bullish prediction**: ✅ if price moved up
            - **Bearish prediction**: ✅ if price moved down
            - **Neutral prediction**: ✅ if price stayed within threshold
            
            ### 4. Movement Threshold
            - Default: 0.05% for Forex, adjusted for volatility
            - Higher for commodities/indices (e.g., 0.25% for Gold)
            - Uses ATR (Average True Range) when available
            
            ## Verification Workflow
            
            ### Step 1: Wait for Market Close
            - Predictions need at least 1 full day to verify
            - Wait for next day's close price
            - Intraday verification not supported
            
            ### Step 2: Run Verification
            - Go to **Verification** tab
            - Click "Verify All Predictions"
            - System fetches actual market data
            - Compares with predictions
            
            ### Step 3: Review Results
            - **Overall Accuracy**: Total correct predictions %
            - **By Symbol**: Accuracy for each trading pair
            - **By Bias Type**: Success rate for bullish/bearish/neutral
            
            ### Step 4: Retrain if Needed
            - If accuracy < 70%, consider retraining
            - Click "Run Adaptive Retraining"
            - System adjusts rule weights
            - Improves future predictions
            
            ## Understanding Verification Results
            
            ### Status Icons
            - ✅ **True**: Prediction was correct
            - ❌ **False**: Prediction was incorrect
            - ⏳ **Pending**: Not enough time elapsed
            - ⚠️ **Unable to Verify**: Data unavailable
            
            ### Accuracy Benchmarks
            - **70%+**: Excellent - System is performing well
            - **60-69%**: Good - Acceptable accuracy
            - **50-59%**: Fair - Consider retraining
            - **<50%**: Poor - Definitely retrain
            
            ## When to Retrain
            
            ### Retrain if:
            - Overall accuracy drops below 70%
            - Specific symbol accuracy is poor
            - Market conditions have changed significantly
            - After 50+ verified predictions
            
            ### Don't retrain if:
            - Less than 10 verified predictions
            - Recent accuracy is good (70%+)
            - Market conditions are stable
            """)
        
        elif "Understanding Reports" in help_topic:
            st.markdown("""
            # 📄 Understanding Reports
            
            ## Report Structure
            
            ### Header Section
            ```
            ═══════════════════════════════════════
            Trading Sentiment Analysis Report
            Symbol: GBPUSD
            Date: 2024-01-15 14:30:00 UTC
            ═══════════════════════════════════════
            ```
            
            ### Executive Summary
            - **Final Bias**: Overall market direction
            - **Confidence Level**: How certain the system is
            - **Weighted Score**: Numerical sentiment score
            
            ### Technical Indicator Breakdown
            
            #### 1. EMA 200 Analysis
            - Shows if price is above or below EMA
            - Indicates long-term trend
            - **Above EMA**: Bullish context
            - **Below EMA**: Bearish context
            
            #### 2. RSI (14) Analysis
            - Momentum indicator
            - **> 70**: Overbought (potential reversal)
            - **50-70**: Bullish momentum
            - **30-50**: Bearish momentum
            - **< 30**: Oversold (potential reversal)
            
            #### 3. MACD Analysis
            - Trend strength and reversals
            - **MACD > Signal**: Bullish
            - **MACD < Signal**: Bearish
            - **Crossovers**: Potential trend change
            
            #### 4. Order Block (OB) Analysis
            - Institutional supply/demand zones
            - **Bullish OB**: Strong buying pressure area
            - **Bearish OB**: Strong selling pressure area
            - **None**: No significant blocks detected
            
            #### 5. Fair Value Gap (FVG) Analysis
            - Price imbalances/inefficiencies
            - **Bullish FVG**: Upward price gap to fill
            - **Bearish FVG**: Downward price gap to fill
            - **None**: No significant gaps
            
            ### Timeframe Details
            - Analysis for each timeframe (D1, H4, H1)
            - Bias alignment across timeframes
            - Confluence indicators
            
            ### Reasoning Section
            - Human-readable explanation
            - Key factors influencing the bias
            - Market context
            
            ## Report Formats
            
            ### Text (.txt) Reports
            - **Pros:**
              - Easy to read in any text editor
              - Can be parsed programmatically
              - Small file size
              - Quick to generate
            - **Use for:** Quick review, automated processing
            
            ### PDF Reports
            - **Pros:**
              - Professional appearance
              - Print-ready
              - Consistent formatting
              - Good for sharing
            - **Use for:** Formal documentation, client reports
            
            ## Using Reports Effectively
            
            ### Daily Workflow
            1. **Morning**: Run analysis, generate reports
            2. **Review**: Read executive summary first
            3. **Deep Dive**: Check indicator breakdowns for context
            4. **Decision**: Use bias and confidence for trading decisions
            
            ### Trading Integration
            - **High confidence (>70%) + Strong bias**: Consider the trade
            - **Moderate confidence (50-70%)**: Wait for confirmation
            - **Low confidence (<50%)**: Avoid or use other tools
            
            ### Archiving
            - Reports auto-named with date/time
            - Easy to track historical analysis
            - Compare predictions vs outcomes
            - Learn from past analyses
            """)
        
        elif "Troubleshooting" in help_topic:
            st.markdown("""
            # 🔧 Troubleshooting
            
            ## Common Issues & Solutions
            
            ### MT5 Connection Failed
            
            **Problem**: "MT5 connection failed" or "Cannot connect to MT5"
            
            **Solutions:**
            1. **Check MT5 Terminal**
               - Ensure MT5 is running
               - Verify you're logged in
               - Check terminal says "Connected" (bottom right)
            
            2. **Restart MT5**
               - Close MT5 completely
               - Wait 10 seconds
               - Reopen and login
               - Try connecting again
            
            3. **Check Credentials**
               - Verify login number is correct
               - Verify password is correct
               - Verify server name is exact (e.g., "ExnessKE-MT5Trial9")
            
            4. **Enable Automated Trading**
               - Tools → Options → Expert Advisors
               - Check "Allow automated trading"
               - Check "Allow DLL imports"
               - Click OK and restart MT5
            
            5. **Check Terminal Path**
               - Default: `C:\\Program Files\\MetaTrader 5\\terminal64.exe`
               - Set `MT5_PATH` environment variable if different
            
            ### Analysis Hangs or Takes Too Long
            
            **Problem**: Analysis starts but never completes
            
            **Solutions:**
            1. **Reduce Symbols**
               - Try analyzing 1-2 symbols first
               - Add more once working
            
            2. **Check Data Availability**
               - Go to Health tab
               - Click "Check Data Access"
               - Ensure you can fetch data
            
            3. **Check Internet Connection**
               - Stable internet required for data fetching
               - Reconnect if unstable
            
            4. **Restart Application**
               - Stop Streamlit (Ctrl+C)
               - Restart: `streamlit run gui.py`
            
            ### No Data Retrieved
            
            **Problem**: "No data retrieved" or "DataFrame is empty"
            
            **Solutions:**
            1. **Verify Symbol Name**
               - Use exact MT5 symbol names
               - Check in MT5 Market Watch
               - Common: GBPUSD, EURUSD, XAUUSD (no dots/dashes)
            
            2. **Enable Symbol in MT5**
               - Right-click Market Watch in MT5
               - Select "Show All"
               - Find and enable the symbol
            
            3. **Check Market Hours**
               - Some markets closed on weekends
               - Historical data still available
            
            4. **Use Fallback Data**
               - Enable "Allow synthetic fallback" in Settings
               - Uses generated data if MT5 unavailable
            
            ### Verification Shows "Unable to Verify"
            
            **Problem**: All predictions show "Unable to Verify"
            
            **Solutions:**
            1. **Wait Longer**
               - Need at least 1 full day after prediction
               - Wait for next trading day close
            
            2. **Check MT5 Connection**
               - Verification needs MT5 data
               - Ensure MT5 is connected
            
            3. **Check Date Range**
               - Very old predictions may have data gaps
               - Focus on recent predictions (< 30 days)
            
            ### Excel File Errors
            
            **Problem**: "Permission denied" or "Excel file corrupt"
            
            **Solutions:**
            1. **Close Excel**
               - Close sentiment_log.xlsx if open in Excel
               - Try operation again
            
            2. **Check Permissions**
               - Ensure write permissions for directory
               - Run as administrator if needed (Windows)
            
            3. **Delete and Regenerate**
               - Backup sentiment_log.xlsx
               - Delete the file
               - Run new analysis (creates new file)
            
            ### Reports Not Generating
            
            **Problem**: No reports in Reports tab
            
            **Solutions:**
            1. **Check Reports Directory**
               - Ensure `reports/` folder exists
               - Create manually if missing
            
            2. **Run Full Analysis**
               - Go to Analysis tab
               - Use "Automatic" mode
               - Wait for "Analysis completed successfully!"
            
            3. **Check File Permissions**
               - Health tab → "Check File Permissions"
               - Ensure reports directory is writable
            
            ## Still Having Issues?
            
            ### Run System Health Check
            1. Go to **Health** tab
            2. Click "Run Health Check"
            3. Review all components
            4. Address any ❌ failures
            
            ### Check Status Monitor
            1. Go to **Status Monitor** tab
            2. Look for ERROR messages
            3. Review details for specific errors
            4. Use error messages to diagnose
            
            ### Advanced: Check Logs
            - Look for console output where Streamlit is running
            - Error messages often show the root cause
            - Share error messages if seeking help
            """)
        
        elif "MT5 Connection Issues" in help_topic:
            st.markdown("""
            # 🔌 MT5 Connection Issues
            
            ## Connection Stuck
            
            If MT5 connection attempts hang or freeze:
            
            ### Immediate Fix
            1. **Stop Streamlit** (Ctrl+C in terminal)
            2. **Close MT5 completely**
            3. **Wait 10 seconds**
            4. **Reopen MT5 and login**
            5. **Restart Streamlit**
            6. **Try connecting again**
            
            ### Prevent Future Hangs
            1. **Ensure MT5 is running BEFORE starting dashboard**
            2. **Keep MT5 logged in**
            3. **Don't close MT5 while dashboard is running**
            4. **Use stable internet connection**
            
            ## Connection Refused
            
            ### Error: "Connection refused" or "Cannot initialize MT5"
            
            **Causes:**
            - MT5 not running
            - MT5 not logged in
            - Wrong terminal path
            - Automated trading disabled
            
            **Solutions:**
            1. Verify MT5 terminal is running
            2. Check you're logged into MT5
            3. Enable automated trading in MT5:
               - Tools → Options → Expert Advisors
               - ✓ Allow automated trading
               - ✓ Allow DLL imports
            
            ## Invalid Credentials
            
            ### Error: "Invalid credentials" or "Authorization failed"
            
            **Check:**
            - Login number (e.g., 12345678)
            - Password (case-sensitive)
            - Server name (exact match, e.g., "ExnessKE-MT5Trial9")
            
            **Common Mistakes:**
            - Extra spaces in password
            - Wrong account (live vs demo)
            - Server name typo
            
            **Fix:**
            1. Open MT5 → Tools → Options → Server
            2. Copy exact login and server
            3. Verify password
            4. Update in dashboard settings
            
            ## Terminal Path Issues
            
            ### Error: "Terminal not found" or "Path does not exist"
            
            **Default Paths:**
            - Windows: `C:\\Program Files\\MetaTrader 5\\terminal64.exe`
            - Windows (x86): `C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe`
            
            **Custom Path:**
            Set environment variable `MT5_PATH` to your installation path:
            ```
            set MT5_PATH=C:\\Your\\Custom\\Path\\terminal64.exe
            ```
            
            ## Slow Connection
            
            If connection is very slow (>30 seconds):
            
            ### Causes:
            - Slow internet
            - MT5 terminal loading
            - Server response time
            
            ### Solutions:
            - Check internet speed
            - Use wired connection instead of WiFi
            - Try different time of day
            - Contact broker if persistent
            
            ## Data Access After Connection
            
            Connected but can't fetch data:
            
            ### Check Symbol Availability
            1. Open MT5 Market Watch
            2. Right-click → "Show All"
            3. Verify symbol appears
            4. If missing, enable from Symbols list
            
            ### Check Symbol Name Format
            - Use MT5's exact symbol name
            - May differ by broker (GBPUSD vs GBPUSDm)
            - Check in MT5 Market Watch for exact name
            """)
        
        elif "About the System" in help_topic:
            st.markdown("""
            # 🤖 About the Trading Sentiment Analysis System
            
            ## Overview
            
            This is an **automated trading sentiment analysis system** that combines:
            - Technical analysis indicators
            - Market structure analysis  
            - Machine learning-based prediction
            - Adaptive retraining capabilities
            
            ## Key Components
            
            ### 1. Data Manager
            - Fetches market data from MT5
            - Fallback to Yahoo Finance if MT5 unavailable
            - Supports multiple timeframes
            - Handles data normalization and validation
            
            ### 2. Structure Analyzer
            - Detects order blocks (institutional zones)
            - Identifies fair value gaps
            - Analyzes higher highs/lower lows
            - Market structure scoring
            
            ### 3. Sentiment Engine
            - Combines multiple indicators
            - Weighted scoring system
            - Confidence calculation
            - Rule-based decision making
            
            ### 4. Verifier
            - Compares predictions vs actual outcomes
            - Calculates accuracy metrics
            - Per-symbol and per-bias tracking
            - Historical performance analysis
            
            ### 5. Auto-Retrainer
            - Monitors prediction accuracy
            - Adjusts rule weights automatically
            - Threshold-based triggering
            - Continuous improvement loop
            
            ### 6. Report Generator
            - Creates detailed analysis reports
            - Multiple format support (TXT, PDF)
            - Timestamped archiving
            - Professional formatting
            
            ## Methodology
            
            ### Technical Indicators (60% weight)
            - **EMA 200**: Trend direction
            - **RSI 14**: Momentum
            - **MACD**: Trend strength
            
            ### Market Structure (40% weight)
            - **Order Blocks**: Supply/demand zones
            - **Fair Value Gaps**: Price inefficiencies
            
            ### Scoring Algorithm
            1. Calculate individual indicator biases (-1 to +1)
            2. Apply weights to each indicator
            3. Sum weighted scores
            4. Normalize to -100 to +100 scale
            5. Determine final bias and confidence
            
            ### Bias Determination
            - **Score > +20**: Bullish
            - **Score -20 to +20**: Neutral
            - **Score < -20**: Bearish
            
            ### Confidence Calculation
            ```
            Confidence = |Weighted Score| / 100 * Agreement Factor
            ```
            - Agreement Factor: How aligned indicators are
            - Higher agreement = higher confidence
            
            ## Adaptive Learning
            
            The system improves over time through:
            
            1. **Verification**: Tracks prediction accuracy
            2. **Performance Analysis**: Identifies weak indicators
            3. **Weight Adjustment**: Increases weight of accurate indicators
            4. **Retesting**: Validates improvements
            
            ## Limitations
            
            ### What This System DOES
            - Provides sentiment analysis
            - Identifies market bias
            - Tracks prediction accuracy
            - Improves over time
            
            ### What This System DOES NOT Do
            - Execute trades automatically
            - Guarantee profits
            - Predict exact price levels
            - Replace human judgment
            
            ## Best Practices
            
            1. **Use as Decision Support**: Not sole trading signal
            2. **Combine with Other Analysis**: Fundamentals, news, etc.
            3. **Verify Regularly**: Check accuracy weekly
            4. **Retrain When Needed**: If accuracy drops below 70%
            5. **Start with Demo**: Test before live trading
            6. **Risk Management**: Always use stop losses
            
            ## Disclaimer
            
            ⚠️ **Important:**
            - This system is for educational/informational purposes
            - Past performance does not guarantee future results
            - Trading involves substantial risk of loss
            - Always do your own research
            - Never trade with money you can't afford to lose
            - Consult a financial advisor before trading
            
            ## Technical Stack
            
            - **Python 3.8+**
            - **Streamlit**: Web interface
            - **MetaTrader 5**: Market data
            - **pandas**: Data processing
            - **openpyxl**: Excel handling
            - **reportlab**: PDF generation
            
            ## Version & Updates
            
            - **Current Version**: 2.0
            - **Last Updated**: 2024
            - **License**: MIT (check LICENSE file)
            """)
        
        elif "Configuration Guide" in help_topic:
            st.markdown("""
            # ⚙️ Configuration Guide
            
            ## Symbol Configuration
            
            ### Adding Symbols
            1. Open sidebar
            2. Expand "📊 Trading Symbols"
            3. Enter symbols (comma or newline separated)
            4. Click "Apply Symbols"
            
            ### Symbol Format
            - Use MT5 exact symbol names
            - No spaces, dots, or dashes unless MT5 uses them
            - Common formats:
              - Forex: GBPUSD, EURUSD
              - Metals: XAUUSD, XAGUSD
              - Indices: US30, SPX500
              - Crypto: BTCUSD, ETHUSD
            
            ### Recommended Symbols
            - **Beginner**: 2-3 major pairs (EURUSD, GBPUSD)
            - **Intermediate**: 5-7 diverse symbols
            - **Advanced**: 10+ across asset classes
            
            ## Settings Configuration
            
            ### Allow Synthetic Fallback
            - **ON**: Uses generated data if MT5/Yahoo fail
            - **OFF**: Requires real market data
            - **Recommended**: ON for reliability
            
            ### Show Operation Logs
            - **ON**: Shows detailed process logs
            - **OFF**: Cleaner interface, essential info only
            - **Recommended**: ON for troubleshooting, OFF for daily use
            
            ### Auto-refresh Data
            - **ON**: Refreshes displays automatically
            - **OFF**: Manual refresh only
            - **Recommended**: OFF (saves resources), use for monitoring only
            
            ## MT5 Configuration
            
            ### Method 1: Environment Variables (Recommended)
            
            Set system environment variables:
            ```
            MT5_LOGIN=12345678
            MT5_PASSWORD=yourpassword
            MT5_SERVER=YourBroker-Server1
            MT5_PATH=C:\\Program Files\\MetaTrader 5\\terminal64.exe
            ```
            
            **Advantages:**
            - Credentials not in code
            - Automatic connection
            - More secure
            
            ### Method 2: Manual Connection
            - Leave environment variables unset
            - Use "Connect MT5" button in GUI
            - Enter credentials when prompted
            
            ## Advanced Configuration
            
            ### Rule Weights (config/rule_weights.json)
            ```json
            {
              "ema_weight": 0.25,
              "rsi_weight": 0.20,
              "macd_weight": 0.15,
              "ob_weight": 0.20,
              "fvg_weight": 0.20
            }
            ```
            
            ### Verification Thresholds
            Set movement thresholds for different symbols:
            ```
            VERIFIER_THRESHOLD_MAP=XAUUSD:0.25,BTCUSD:1.0,DEFAULT:0.05
            ```
            
            ### Lookback Periods
            - Default: 250 days for daily data
            - Minimum: 200 days (for EMA 200 calculation)
            - Recommended: 250-365 days
            
            ## File Locations
            
            ### Data Files
            - **Sentiment Log**: `sentiment_log.xlsx`
            - **Reports**: `reports/` directory
            - **Config**: `config/` directory
            
            ### Configuration Files
            - **Rule Weights**: `config/rule_weights.json`
            - **GUI Config**: `config/gui_config.json` (Tkinter GUI only)
            
            ## Backup & Recovery
            
            ### Important Files to Backup
            1. `sentiment_log.xlsx` - All predictions and verification data
            2. `config/rule_weights.json` - Trained model weights
            3. `reports/` - Historical analysis reports
            
            ### Restore from Backup
            1. Stop the application
            2. Copy backup files to original locations
            3. Restart the application
            4. Verify data in Status Monitor tab
            
            ## Performance Tuning
            
            ### For Faster Analysis
            - Reduce number of symbols
            - Use shorter lookback periods (e.g., 200 days)
            - Analyze during off-peak hours
            
            ### For Higher Accuracy
            - Increase lookback period (365+ days)
            - Verify frequently (daily)
            - Retrain when accuracy < 70%
            - Focus on liquid, high-volume symbols
            
            ### For Resource Efficiency
            - Disable auto-refresh
            - Reduce Status Monitor event count
            - Close unused tabs
            - Clear cache periodically
            """)
        
        else:
            st.info("Select a topic from the dropdown above to view help documentation.")
        
        # Quick links
        st.markdown("---")
        st.subheader("⚡ Quick Links")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📖 Getting Started**
            - First-time setup
            - Initial configuration
            - Running first analysis
            """)
        
        with col2:
            st.markdown("""
            **🔧 Troubleshooting**
            - Connection issues
            - Data problems
            - Error messages
            """)
        
        with col3:
            st.markdown("""
            **📚 Advanced**
            - Configuration files
            - Custom thresholds
            - Performance tuning
            """)


if __name__ == "__main__":
    main()
