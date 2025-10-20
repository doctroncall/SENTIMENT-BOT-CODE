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


def render_data_collection_status(dashboard: Dashboard) -> None:
    """Render real-time MT5 data collection status window"""
    st.subheader("📊 MT5 Data Collection Status")
    
    try:
        # Import the tracker
        from data_manager import get_collection_status
        tracker = get_collection_status()
        status = tracker.get_status()
        
        # Status indicator
        if status['current_status'] == 'idle':
            st.info("💤 **Status:** Idle - No active data collection")
        elif status['current_status'] == 'connecting':
            st.warning("🔌 **Status:** Connecting to MT5...")
        elif status['current_status'] == 'fetching':
            st.success(f"📡 **Status:** Fetching data - {status['current_symbol']} {status['current_timeframe'] or ''}")
        elif status['current_status'] == 'processing':
            st.success(f"⚙️ **Status:** Processing data...")
        elif status['current_status'] == 'error':
            st.error(f"❌ **Status:** Error - {status.get('error_message', 'Unknown error')}")
        else:
            st.info("💤 **Status:** Ready")
        
        # Progress metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = status.get('total_symbols', 0)
            st.metric("Total Symbols", total)
        
        with col2:
            completed = len(status.get('symbols_completed', []))
            st.metric("✅ Completed", completed)
        
        with col3:
            failed = len(status.get('symbols_failed', []))
            st.metric("❌ Failed", failed, delta_color="inverse")
        
        with col4:
            queued = len(status.get('symbols_queue', []))
            st.metric("⏳ Queued", queued)
        
        # Current operation details
        if status['current_symbol']:
            st.markdown("---")
            st.markdown(f"**🎯 Current Symbol:** `{status['current_symbol']}`")
            
            # Show timeframe data for current symbol
            tf_data = status.get('timeframe_data', {}).get(status['current_symbol'], {})
            if tf_data:
                st.markdown("**Timeframe Collection:**")
                
                tf_cols = st.columns(len(tf_data))
                for idx, (tf, data) in enumerate(tf_data.items()):
                    with tf_cols[idx]:
                        bars = data.get('bars', 0)
                        tf_status = data.get('status', 'unknown')
                        
                        if tf_status == 'complete':
                            st.success(f"{tf}\n{bars} bars ✅")
                        elif tf_status == 'fetching':
                            st.info(f"{tf}\nFetching... ⏳")
                        elif tf_status == 'failed':
                            st.error(f"{tf}\nFailed ❌")
                        elif tf_status == 'empty':
                            st.warning(f"{tf}\nNo data ⚠️")
                        else:
                            st.text(f"{tf}\n...")
        
        # Completed symbols summary
        if status.get('symbols_completed'):
            with st.expander("✅ Completed Symbols", expanded=False):
                for sym in status['symbols_completed']:
                    tf_data = status.get('timeframe_data', {}).get(sym, {})
                    total_bars = sum(data.get('bars', 0) for data in tf_data.values())
                    tf_count = len([d for d in tf_data.values() if d.get('status') == 'complete'])
                    st.text(f"✅ {sym}: {tf_count} timeframes, {total_bars} total bars")
        
        # Failed symbols
        if status.get('symbols_failed'):
            with st.expander("❌ Failed Symbols", expanded=False):
                for sym in status['symbols_failed']:
                    st.text(f"❌ {sym}")
        
        # Last update timestamp
        if status.get('last_update'):
            st.caption(f"🕒 Last updated: {status['last_update'].strftime('%H:%M:%S')}")
        
    except Exception as e:
        st.error(f"❌ Error rendering data collection status: {e}")


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
    
    # Data Collection Status Window (NEW!)
    with st.container():
        render_data_collection_status(dashboard)
    
    st.markdown("---")
    
    # System Metrics Dashboard
    with st.container():
        render_system_metrics(dashboard)
    
    st.markdown("---")
    
    # ============================================================
    # TABBED INTERFACE - 5 TABS AS REQUESTED
    # ============================================================
    # TABBED INTERFACE - 5 CLEAN TABS
    # ============================================================
    tab_home, tab_analysis, tab_health, tab_retrain, tab_running_status = st.tabs([
        "🏠 Home",
        "📊 Analysis",
        "🏥 Health",
        "🔄 Retrain",
        "📡 Running Status"
    ])
    
    # ============================================================
    # TAB 1: HOME - ALL IMPORTANT INFO
    # ============================================================
    with tab_home:
        st.header("🏠 Trading Bot - Complete Dashboard")
        
        # Quick Actions Row
        st.subheader("⚡ Quick Actions")
        
        # Info box explaining the difference
        st.info("""
        💡 **Button Guide:**
        - **Run Full Analysis** = Analyze ALL configured symbols (see Symbol Configuration below)
        - **Analyze Single Symbol** = Analyze ONE specific symbol you enter
        """)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**📊 ALL Symbols**")
            if st.button(
                "▶️ Run Full Analysis", 
                type="primary", 
                use_container_width=True,
                help=f"Analyze ALL {len(dashboard.symbols)} configured symbols: {', '.join(dashboard.symbols)}"
            ):
                with st.spinner(f"Running analysis for {len(dashboard.symbols)} symbols..."):
                    result, out, err = capture_output(dashboard.run_full_cycle)
                if err:
                    st.error(f"❌ Error: {err}")
                else:
                    st.success("✅ Complete!")
                    st.rerun()
        
        with col2:
            st.markdown("**🎯 Single Symbol**")
            manual_sym = st.text_input(
                "Enter Symbol", 
                placeholder="e.g., GBPUSD", 
                key="home_sym",
                help="Enter any trading symbol (e.g., GBPUSD, XAUUSD, EURUSD)"
            )
            if st.button(
                "🎯 Analyze This Symbol", 
                use_container_width=True,
                help="Analyze only the specific symbol you entered above"
            ):
                if manual_sym.strip():
                    with st.spinner(f"Analyzing {manual_sym}..."):
                        result, out, err = capture_output(dashboard.run_manual_analysis, manual_sym.strip())
                    if not err:
                        st.success(f"✅ Done!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a symbol first")
        
        with col3:
            if st.button("✅ Verify All", type="secondary", use_container_width=True):
                with st.spinner("Verifying..."):
                    _, out, err = capture_output(dashboard.run_verification)
                if not err:
                    st.success("✅ Verified!")
                    st.rerun()
        
        with col4:
            if st.button("🔄 Retrain Model", type="secondary", use_container_width=True):
                with st.spinner("Retraining..."):
                    _, out, err = capture_output(dashboard.run_retrain)
                if not err:
                    st.success("✅ Retrained!")
                    st.rerun()
        
        st.markdown("---")
        
        # System Status
        st.subheader("📊 System Status")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        mt5_status = get_mt5_status(dashboard)
        excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
        
        with col1:
            if mt5_status['connected']:
                st.metric("MT5", "🟢 Connected")
            else:
                st.metric("MT5", "🔴 Offline")
        
        with col2:
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file)
                st.metric("Predictions", len(df))
            else:
                st.metric("Predictions", 0)
        
        with col3:
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file)
                if "Verified" in df.columns:
                    verified = df["Verified"].isin(["✅ True", "❌ False"]).sum()
                    st.metric("Verified", verified)
                else:
                    st.metric("Verified", 0)
            else:
                st.metric("Verified", 0)
        
        with col4:
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file)
                if "Verified" in df.columns:
                    verified_df = df[df["Verified"].isin(["✅ True", "❌ False"])]
                    if len(verified_df) > 0:
                        acc = (verified_df["Verified"] == "✅ True").sum() / len(verified_df) * 100
                        st.metric("Accuracy", f"{acc:.1f}%")
                    else:
                        st.metric("Accuracy", "N/A")
                else:
                    st.metric("Accuracy", "N/A")
            else:
                st.metric("Accuracy", "N/A")
        
        with col5:
            if os.path.exists("reports"):
                reports = len([f for f in os.listdir("reports") if os.path.isfile(os.path.join("reports", f))])
                st.metric("Reports", reports)
            else:
                st.metric("Reports", 0)
        
        st.markdown("---")
        
        # Accuracy Metrics
        st.subheader("📈 Accuracy Breakdown")
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            if "Verified" in df.columns:
                verified_df = df[df["Verified"].isin(["✅ True", "❌ False"])]
                if not verified_df.empty:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        correct = (verified_df["Verified"] == "✅ True").sum()
                        total = len(verified_df)
                        acc = correct / total * 100
                        st.progress(acc / 100)
                        st.markdown(f"**{acc:.1f}%** overall ({correct}/{total})")
                    
                    with col_b:
                        if "Symbol" in verified_df.columns:
                            for sym in verified_df["Symbol"].unique():
                                sym_df = verified_df[verified_df["Symbol"] == sym]
                                sym_acc = (sym_df["Verified"] == "✅ True").sum() / len(sym_df) * 100
                                st.text(f"{sym}: {sym_acc:.0f}%")
                else:
                    st.info("No verified predictions")
            else:
                st.info("No verification data")
        else:
            st.info("No data yet")
        
        st.markdown("---")
        
        # Configuration
        st.subheader("⚙️ Symbol Configuration")
        col_cfg1, col_cfg2 = st.columns([3, 1])
        with col_cfg1:
            syms_input = st.text_area(
                "Symbols (comma-separated)",
                value=", ".join(dashboard.symbols),
                height=80
            )
        with col_cfg2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save", type="primary", use_container_width=True):
                syms = parse_symbols(syms_input)
                if syms:
                    dashboard.symbols = syms
                    st.success(f"Saved {len(syms)} symbols")
                    st.rerun()
        
        st.markdown("---")
        
        # Recent Predictions Table
        st.subheader("📋 Recent Predictions")
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            if not df.empty:
                cols = [c for c in ["Date", "Symbol", "Final Bias", "Confidence", "Verified", "Weighted Score"] if c in df.columns]
                st.dataframe(df[cols].tail(20).sort_values("Date", ascending=False), use_container_width=True, hide_index=True, height=400)
            else:
                st.info("No predictions")
        else:
            st.info("No data file")
        
        st.markdown("---")
        
        # Recent Reports
        st.subheader("📄 Recent Reports")
        if os.path.exists("reports"):
            files = sorted([f for f in os.listdir("reports") if os.path.isfile(os.path.join("reports", f))], 
                          key=lambda x: os.path.getmtime(os.path.join("reports", x)), reverse=True)[:10]
            if files:
                for f in files:
                    col_r1, col_r2 = st.columns([3, 1])
                    with col_r1:
                        st.text(f"📄 {f}")
                    with col_r2:
                        with open(os.path.join("reports", f), "rb") as fh:
                            st.download_button("⬇️", fh.read(), file_name=f, key=f"dl_{f}")
            else:
                st.info("No reports")
        else:
            st.info("No reports folder")
    
    # ============================================================
    # TAB 2: ANALYSIS - RESULTS ONLY (NO RUN BUTTONS)
    # ============================================================
    with tab_analysis:
        st.header("📊 Analysis Results")
        st.markdown("*View completed analysis results and predictions. Use the Home tab to run new analyses.*")
        
        st.markdown("---")
        
        st.subheader("📈 Analysis Summary")
        excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            if not df.empty:
                # Summary metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total Analyses", len(df))
                with col2:
                    st.metric("Symbols Tracked", df["Symbol"].nunique() if "Symbol" in df.columns else 0)
                with col3:
                    if "Date" in df.columns:
                        st.metric("Last Analysis", pd.to_datetime(df["Date"]).max().strftime("%Y-%m-%d"))
                    else:
                        st.metric("Last Analysis", "N/A")
                with col4:
                    today = datetime.now().strftime("%Y-%m-%d")
                    today_count = (df["Date"].astype(str).str.contains(today)).sum() if "Date" in df.columns else 0
                    st.metric("Today's Analyses", today_count)
                with col5:
                    if "Verified" in df.columns:
                        verified_df = df[df["Verified"].isin(["✅ True", "❌ False"])]
                        if len(verified_df) > 0:
                            acc = (verified_df["Verified"] == "✅ True").sum() / len(verified_df) * 100
                            st.metric("Accuracy", f"{acc:.1f}%")
                        else:
                            st.metric("Accuracy", "N/A")
                    else:
                        st.metric("Accuracy", "N/A")
                
                st.markdown("---")
                
                # Filters
                st.subheader("🔍 Filter & View Results")
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    sym_filter = st.selectbox("Filter by Symbol", ["All"] + sorted(df["Symbol"].unique().tolist()) if "Symbol" in df.columns else ["All"])
                with col_f2:
                    bias_filter = st.selectbox("Filter by Bias", ["All"] + sorted(df["Final Bias"].unique().tolist()) if "Final Bias" in df.columns else ["All"])
                with col_f3:
                    count_filter = st.selectbox("Show Entries", [10, 20, 50, 100, "All"], index=1)
                
                # Apply filters
                filt_df = df.copy()
                if sym_filter != "All":
                    filt_df = filt_df[filt_df["Symbol"] == sym_filter]
                if bias_filter != "All":
                    filt_df = filt_df[filt_df["Final Bias"] == bias_filter]
                
                # Display filtered results
                cols = [c for c in ["Date", "Symbol", "Final Bias", "Confidence", "Weighted Score", "Verified"] if c in filt_df.columns]
                if count_filter != "All":
                    display_df = filt_df[cols].tail(count_filter).sort_values("Date", ascending=False)
                else:
                    display_df = filt_df[cols].sort_values("Date", ascending=False)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
                
                # Export option
                st.markdown("---")
                col_export1, col_export2 = st.columns([3, 1])
                with col_export1:
                    st.markdown("**💾 Export Results**")
                with col_export2:
                    csv = display_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("📝 No analysis results yet. Go to the Home tab and click 'Run Full Analysis' to generate predictions.")
        else:
            st.info("📝 No analysis data file found. Run your first analysis from the Home tab to get started.")
    
    # ============================================================
    # TAB 3: HEALTH - DIAGNOSTICS
    # ============================================================
    with tab_health:
        st.header("🏥 System Health")
        
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            st.markdown("**Run comprehensive system health check**")
        with col_h2:
            run_health = st.button("🔍 Run Health Check", type="primary", use_container_width=True)
        
        if run_health:
            with st.spinner("Running health check..."):
                ok, out, err = capture_output(dashboard.health_check)
            if err:
                st.error("Health check failed")
            elif ok:
                st.success("All systems OK")
            else:
                st.warning("Some issues detected")
            if show_logs and out:
                with st.expander("Details", expanded=True):
                    st.text(out)
        
        st.markdown("---")
        
        st.subheader("🔧 Component Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Core**")
            st.text(f"{'✅' if dashboard else '❌'} Dashboard")
            st.text(f"{'✅' if hasattr(dashboard, 'data_manager') else '❌'} Data Manager")
            st.text(f"{'✅' if hasattr(dashboard, 'sentiment_engine') else '❌'} Sentiment Engine")
        
        with col2:
            st.markdown("**Connections**")
            mt5_s = get_mt5_status(dashboard)
            st.text(f"{'✅' if mt5_s['connected'] else '❌'} MT5")
            st.text(f"{'✅' if os.path.exists('sentiment_log.xlsx') else '❌'} Excel Log")
            st.text(f"{'✅' if os.path.exists('config') else '❌'} Config Dir")
        
        with col3:
            st.markdown("**Modules**")
            st.text(f"{'✅' if hasattr(dashboard, 'verifier') else '❌'} Verifier")
            st.text(f"{'✅' if hasattr(dashboard, 'retrainer') else '❌'} Retrainer")
            st.text(f"{'✅' if hasattr(dashboard, 'report_generator') else '❌'} Reports")
        
        st.markdown("---")
        
        st.subheader("⚡ Quick Tests")
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            if st.button("🔌 Test MT5", use_container_width=True):
                if mt5_s['enabled']:
                    if dashboard.data_manager.is_connected():
                        st.success("✅ Connected")
                    else:
                        connected = dashboard.data_manager.connect()
                        if connected:
                            st.success("✅ Connected")
                        else:
                            st.error("❌ Failed")
                else:
                    st.warning("MT5 disabled")
        
        with col_t2:
            if st.button("📊 Test Data", use_container_width=True):
                test_sym = dashboard.symbols[0] if dashboard.symbols else "GBPUSD"
                df = dashboard.data_manager.fetch_ohlcv_for_timeframe(test_sym, "D1", lookback_days=5)
                if df is not None and not df.empty:
                    st.success(f"✅ Got {len(df)} bars")
                else:
                    st.error("❌ No data")
        
        with col_t3:
            if st.button("📄 Test Files", use_container_width=True):
                checks = []
                if os.path.exists('sentiment_log.xlsx'):
                    checks.append(("Excel readable", os.access('sentiment_log.xlsx', os.R_OK)))
                    checks.append(("Excel writable", os.access('sentiment_log.xlsx', os.W_OK)))
                all_ok = all(c[1] for c in checks) if checks else False
                if all_ok:
                    st.success("✅ All OK")
                else:
                    st.warning("⚠️ Issues")
    
    # ============================================================
    # TAB 4: RETRAIN - MODEL RETRAINING
    # ============================================================
    with tab_retrain:
        st.header("🔄 Model Retraining")
        
        st.subheader("📊 Current Performance")
        excel_file = getattr(dashboard, "excel_file", "sentiment_log.xlsx")
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            if "Verified" in df.columns:
                verified_df = df[df["Verified"].isin(["✅ True", "❌ False"])]
                if not verified_df.empty:
                    correct = (verified_df["Verified"] == "✅ True").sum()
                    total = len(verified_df)
                    acc = correct / total * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Accuracy", f"{acc:.1f}%")
                    with col2:
                        st.metric("Verified", total)
                    with col3:
                        st.metric("Correct", correct)
                    
                    if acc < 70:
                        st.warning(f"⚠️ Accuracy ({acc:.1f}%) is below 70% - retraining recommended")
                    else:
                        st.success(f"✅ Accuracy ({acc:.1f}%) is good")
                else:
                    st.info("No verified predictions yet")
            else:
                st.info("No verification data")
        else:
            st.info("No data file")
        
        st.markdown("---")
        
        st.subheader("🔄 Retrain Model")
        col_r1, col_r2 = st.columns([2, 1])
        
        with col_r1:
            st.markdown("""
            **Retraining adjusts rule weights based on verified predictions**
            - Improves accuracy over time
            - Adapts to market conditions
            - Run when accuracy < 70%
            """)
        
        with col_r2:
            if st.button("▶️ Run Retraining", type="primary", use_container_width=True):
                with st.spinner("Retraining model..."):
                    _, out, err = capture_output(dashboard.run_retrain)
                if err:
                    st.error(f"❌ Error: {err}")
                else:
                    st.success("✅ Retraining complete!")
                if show_logs and out:
                    with st.expander("Retrain Logs"):
                        st.text(out)
    
    # ============================================================
    # TAB 5: RUNNING STATUS - LIVE LOG
    # ============================================================
    with tab_running_status:
        render_status_monitor()


if __name__ == "__main__":
    main()
