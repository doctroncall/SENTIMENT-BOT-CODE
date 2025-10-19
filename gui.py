import os
import io
import contextlib
import traceback
from typing import List, Tuple, Optional

import pandas as pd

try:
    import streamlit as st
except Exception as e:
    raise RuntimeError("Streamlit is required to run the GUI. Install with: pip install streamlit") from e

# Local imports
from dashboard import Dashboard


def ensure_dashboard() -> Dashboard:
    """Create or fetch a persistent Dashboard instance in session state."""
    if "dashboard" not in st.session_state:
        st.session_state.dashboard = Dashboard()
    return st.session_state.dashboard


def parse_symbols(input_text: str) -> List[str]:
    symbols = [s.strip() for s in input_text.replace("\n", ",").split(",") if s.strip()]
    # Normalize here to reduce user errors; Dashboard also normalizes
    return symbols


def capture_output(fn, *args, **kwargs) -> Tuple[Optional[object], str, Optional[BaseException]]:
    """Run a function while capturing stdout prints. Returns (result, output_text, error)."""
    buffer = io.StringIO()
    result = None
    err: Optional[BaseException] = None
    with contextlib.redirect_stdout(buffer):
        try:
            result = fn(*args, **kwargs)
        except BaseException as e:  # capture all to display nicely in UI
            err = e
            traceback.print_exc()
    return result, buffer.getvalue(), err


def render_latest_log_table(excel_file: str) -> None:
    st.subheader("Latest Sentiment Log")
    if not os.path.exists(excel_file):
        st.info("No sentiment log file found yet. Run an analysis first.")
        return
    try:
        df = pd.read_excel(excel_file)
        if df.empty:
            st.info("Sentiment log is empty.")
            return
        # Show last 20 entries by date
        display_cols = [
            col for col in ["Date", "Symbol", "Final Bias", "Confidence", "Verified", "Weighted Score"]
            if col in df.columns
        ]
        st.dataframe(df.tail(20)[display_cols], use_container_width=True)
    except Exception as e:
        st.error(f"Could not read {excel_file}: {e}")


def render_reports_section(report_dir: str) -> None:
    st.subheader("Reports")
    if not os.path.isdir(report_dir):
        st.info("No reports directory yet.")
        return
    files = sorted(
        [f for f in os.listdir(report_dir) if os.path.isfile(os.path.join(report_dir, f))],
        reverse=True,
    )
    if not files:
        st.info("No reports generated yet.")
        return
    selection = st.selectbox("Select a report to view/download", files, index=0)
    if selection:
        path = os.path.join(report_dir, selection)
        st.write(f"Selected: `{selection}`")
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            mime = "application/pdf" if selection.lower().endswith(".pdf") else "text/plain"
            st.download_button(
                label="Download report",
                data=data,
                file_name=selection,
                mime=mime,
                use_container_width=True,
            )
            # For text reports, show inline preview
            if selection.lower().endswith(".txt"):
                try:
                    text = data.decode("utf-8", errors="replace")
                    st.text_area("Report preview", value=text, height=300)
                except Exception:
                    pass
        except Exception as e:
            st.error(f"Failed to open report: {e}")


def main() -> None:
    st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")
    st.title("🤖 Trading Bot Dashboard")

    dashboard = ensure_dashboard()

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        default_symbols = ", ".join(dashboard.symbols) if hasattr(dashboard, "symbols") else "GBPUSD, XAUUSD"
        symbols_text = st.text_area("Symbols (comma or newline separated)", value=default_symbols, height=100)
        colA, colB = st.columns(2)
        with colA:
            allow_synth = st.toggle("Allow synthetic fallback", value=True, help="If enabled, synthetic data is used when both MT5 and Yahoo fail.")
        with colB:
            show_logs = st.toggle("Show operation logs", value=True)

        if st.button("Apply Symbols", use_container_width=True):
            symbols = parse_symbols(symbols_text)
            if symbols:
                dashboard.symbols = symbols
                st.success(f"Applied symbols: {', '.join(symbols)}")
            else:
                st.warning("No valid symbols provided.")

        st.divider()
        st.caption("Environment toggles")
        if allow_synth:
            os.environ["ALLOW_SYNTHETIC_DATA"] = "1"
        else:
            os.environ["ALLOW_SYNTHETIC_DATA"] = "0"

    # Tabs for actions
    tab_analyze, tab_verify, tab_status, tab_reports = st.tabs(["Analysis", "Verification & Retrain", "Status", "Reports"])

    with tab_analyze:
        st.subheader("Run Analysis")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run full analysis for configured symbols", type="primary"):
                with st.spinner("Running full analysis..."):
                    result, out, err = capture_output(dashboard.run_full_cycle)
                if err:
                    st.error(f"Analysis failed: {err}")
                else:
                    st.success("Analysis completed.")
                if show_logs and out:
                    with st.expander("Logs"):
                        st.text(out)
        with c2:
            manual_symbol = st.text_input("Manual analysis for a specific symbol", placeholder="e.g., GBPUSD")
            if st.button("Run manual analysis"):
                if manual_symbol.strip():
                    with st.spinner(f"Running manual analysis for {manual_symbol.strip()}..."):
                        result, out, err = capture_output(dashboard.run_manual_analysis, manual_symbol.strip())
                    if err:
                        st.error(f"Manual analysis failed: {err}")
                    else:
                        st.success("Manual analysis completed.")
                    if show_logs and out:
                        with st.expander("Logs"):
                            st.text(out)
                else:
                    st.warning("Enter a symbol to run manual analysis.")

    with tab_verify:
        st.subheader("Verification & Retraining")
        v1, v2 = st.columns(2)
        with v1:
            if st.button("Run verification now"):
                with st.spinner("Verifying predictions..."):
                    _, out, err = capture_output(dashboard.run_verification)
                if err:
                    st.error(f"Verification failed: {err}")
                else:
                    st.success("Verification completed.")
                if show_logs and out:
                    with st.expander("Logs"):
                        st.text(out)
        with v2:
            if st.button("Run retraining now"):
                with st.spinner("Running retraining..."):
                    _, out, err = capture_output(dashboard.run_retrain)
                if err:
                    st.error(f"Retraining failed: {err}")
                else:
                    st.success("Retraining completed.")
                if show_logs and out:
                    with st.expander("Logs"):
                        st.text(out)

        st.divider()
        if st.button("Run health check"):
            with st.spinner("Running health check..."):
                ok, out, err = capture_output(dashboard.health_check)
            # health_check prints its own results and returns bool
            if err:
                st.error(f"Health check failed: {err}")
            else:
                st.success("All systems operational" if ok else "Some systems need attention")
            if show_logs and out:
                with st.expander("Logs"):
                    st.text(out)

    with tab_status:
        st.subheader("System Status")
        # Show latest entries from excel
        render_latest_log_table(getattr(dashboard, "excel_file", "sentiment_log.xlsx"))

        st.divider()
        st.caption("Quick status display from dashboard")
        if st.button("Show status output"):
            with st.spinner("Gathering status..."):
                _, out, err = capture_output(dashboard.show_status)
            if err:
                st.error(f"Status failed: {err}")
            if show_logs and out:
                with st.expander("Status Output"):
                    st.text(out)

    with tab_reports:
        render_reports_section("reports")

    st.divider()
    st.caption("Tip: launch with `streamlit run gui.py`.")


if __name__ == "__main__":
    main()
