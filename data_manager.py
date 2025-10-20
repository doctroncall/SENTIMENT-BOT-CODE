"""
data_manager.py - FIXED VERSION

Responsibilities:
- Connect to MetaTrader5 (MT5) using supplied credentials.
- Fetch OHLCV for requested symbols and timeframes.
- Provide resampled multi-timeframe DataFrames for downstream modules.
- Cache results to disk (data/{symbol}_{tf}.csv).

Fixed Issues:
- Timezone conversion errors
- Symbol normalization consistency
- Better error recovery per symbol
- Data validation improvements
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
import time
import threading

import pandas as pd
import numpy as np

# Optional dependencies (import inside functions to avoid hard failure)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

# Yahoo Finance dependency removed — MT5-only operation

# ----------------------------
# CONFIG (DEV / HARDCODED)
# ----------------------------
# DEV/demo credentials (pull from environment; avoid hardcoded secrets)
# Examples:
#   export MT5_LOGIN=12345678
#   export MT5_PASSWORD="your-password"
#   export MT5_SERVER="YourBroker-Server"
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "211744072") or 211744072)
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z")
MT5_SERVER = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
MT5_PATH = os.getenv("MT5_PATH", r"C:\\Program Files\\MetaTrader 5\\terminal64.exe")

# Data cache folder
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Logging
# Root/basic logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataManager")
logger.propagate = False

# Connection-specific logging to file
connection_logger = logging.getLogger("DataManager.Connection")
connection_logger.setLevel(logging.DEBUG)
# Prevent duplicate messages via root logger handlers
connection_logger.propagate = False
# Reset existing handlers to avoid duplicates on Streamlit reruns
for _h in list(connection_logger.handlers):
    try:
        if hasattr(_h, "close"):
            _h.close()
    except Exception:
        pass
    connection_logger.removeHandler(_h)

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def _is_windows_ansi_console() -> bool:
    """Detect Windows console likely using a non-UTF8 codepage (e.g., cp1252)."""
    encoding = getattr(sys.stdout, "encoding", None) or ""
    return os.name == "nt" and encoding.lower() not in ("utf-8", "utf8", "utf_8")


class ConsoleSafeFormatter(logging.Formatter):
    """Formatter that avoids UnicodeEncodeError on Windows ANSI consoles.

    It preserves Unicode on UTF-8-capable terminals, and degrades gracefully
    on ANSI codepages by replacing a few common symbols with ASCII fallbacks
    and using a safe re-encode with replacement as a last resort.
    """

    _REPLACEMENTS = {
        "✓": "OK",
        "✅": "OK",
        "❌": "X",
        "⚠️": "WARN",
        "⚠": "WARN",
        "📊": "STATS",
        "💡": "TIP",
        "📋": "INFO",
        "→": "->",
        "—": "-",
        "–": "-",
        "…": "...",
    }

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        if not _is_windows_ansi_console():
            return formatted

        # Apply targeted replacements for known symbols first
        for bad, good in self._REPLACEMENTS.items():
            if bad in formatted:
                formatted = formatted.replace(bad, good)

        # Ensure string can be encoded by the active console
        console_encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        try:
            formatted.encode(console_encoding)
            return formatted
        except Exception:
            return formatted.encode(console_encoding, errors="replace").decode(console_encoding, errors="replace")


# File handler for connection logs (force UTF-8 to support Unicode symbols)
connection_log_file = os.path.join(LOGS_DIR, f"mt5_connection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = logging.FileHandler(connection_log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
connection_logger.addHandler(file_handler)

# Also add console handler for connection logger (ASCII-safe on Windows ANSI consoles)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ConsoleSafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
connection_logger.addHandler(console_handler)

logger.info(f"Connection logging enabled: {connection_log_file}")
try:
    print(f"\n📝 Connection logs will be written to: {connection_log_file}\n")
except UnicodeEncodeError:
    print(f"\n[LOG] Connection logs will be written to: {connection_log_file}\n")

# Status monitoring
try:
    from status_monitor import log_connection, log_data_fetch, log_success, log_error, log_warning, log_cache
    STATUS_MONITOR_AVAILABLE = True
except ImportError:
    # Fallback stubs if status_monitor not available
    STATUS_MONITOR_AVAILABLE = False
    def log_connection(msg, details=None): pass
    def log_data_fetch(msg, details=None): pass
    def log_success(msg, details=None): pass
    def log_error(msg, details=None): pass
    def log_warning(msg, details=None): pass
    def log_cache(msg, details=None): pass

# Default symbols list for UX fallbacks when MT5 isn't connected
DEFAULT_SYMBOLS = [
    "GBPUSD", "XAUUSD", "EURUSD", "USDJPY", "AUDUSD",
    "USDCAD", "USDCHF", "NZDUSD", "BTCUSD", "ETHUSD",
]

# Broker-specific symbol variations (for auto-discovery)
# Different brokers use different suffixes: m (mini), .a, .b, etc.
SYMBOL_VARIATIONS = {
    "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.a", "GBPUSD.", "GBPUSD.raw"],
    "XAUUSD": ["XAUUSD", "XAUUSDm", "GOLD", "GOLDm", "XAUUSD.", "XAUUSD.a"],
    "EURUSD": ["EURUSD", "EURUSDm", "EURUSD.a", "EURUSD.", "EURUSD.raw"],
    "USDJPY": ["USDJPY", "USDJPYm", "USDJPY.a", "USDJPY."],
    "AUDUSD": ["AUDUSD", "AUDUSDm", "AUDUSD.a", "AUDUSD."],
    "USDCAD": ["USDCAD", "USDCADm", "USDCAD.a", "USDCAD."],
    "USDCHF": ["USDCHF", "USDCHFm", "USDCHF.a", "USDCHF."],
    "NZDUSD": ["NZDUSD", "NZDUSDm", "NZDUSD.a", "NZDUSD."],
    "BTCUSD": ["BTCUSD", "BTCUSDm", "BTCUSD.", "BTC"],
    "ETHUSD": ["ETHUSD", "ETHUSDm", "ETHUSD.", "ETH"],
}

# Timeframe map (string -> mt5 constant)
MT5_TF_MAP = {
    "M1": mt5.TIMEFRAME_M1 if MT5_AVAILABLE else 1,
    "M5": mt5.TIMEFRAME_M5 if MT5_AVAILABLE else 5,
    "M15": mt5.TIMEFRAME_M15 if MT5_AVAILABLE else 15,
    "H1": mt5.TIMEFRAME_H1 if MT5_AVAILABLE else 60,
    "H4": mt5.TIMEFRAME_H4 if MT5_AVAILABLE else 240,
    "D1": mt5.TIMEFRAME_D1 if MT5_AVAILABLE else 1440,
    "W1": mt5.TIMEFRAME_W1 if MT5_AVAILABLE else 10080,
    "MN1": mt5.TIMEFRAME_MN1 if MT5_AVAILABLE else 43200,
}

# Helper: pandas-friendly column order
# Core OHLCV data (always fetched)
COLUMNS = ["time", "open", "high", "low", "close", "tick_volume"]

# Extended columns (optional, fetched if available from broker)
EXTENDED_COLUMNS = ["real_volume", "spread"]

# Whether to fetch extended data
FETCH_EXTENDED_DATA = os.getenv("FETCH_EXTENDED_DATA", "1").strip() in ("1", "true", "yes", "on")

# MT5 connection behavior (tunable via env)
MT5_ATTACH_FIRST = os.getenv("MT5_ATTACH_FIRST", "1").strip().lower() in ("1", "true", "yes", "on")
MT5_INIT_TIMEOUT_MS = int(os.getenv("MT5_INIT_TIMEOUT_MS", "12000"))
MT5_LOGIN_TIMEOUT_MS = int(os.getenv("MT5_LOGIN_TIMEOUT_MS", "12000"))


def _call_with_timeout(fn, *, timeout_seconds: float, args: Optional[tuple] = None, kwargs: Optional[dict] = None):
    """Run a callable in a daemon thread, returning (completed, result, error).

    This guards against 3rd-party calls that may hang (e.g., mt5.initialize/login).
    """
    args = args or ()
    kwargs = kwargs or {}
    container = {"done": False, "result": None, "error": None}

    def runner():
        try:
            container["result"] = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            container["error"] = exc
        finally:
            container["done"] = True

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if not container["done"]:
        return False, None, TimeoutError(f"Call timed out after {timeout_seconds:.1f}s")
    return True, container["result"], container["error"]


# ----------------------------
# FIXED: Centralized Utility Functions
# ----------------------------
def normalize_symbol(symbol: str) -> str:
    """
    FIXED: Centralized symbol normalization for consistency across the system
    """
    if not symbol:
        return ""
    return symbol.upper().replace("/", "").replace("_", "").replace(" ", "").strip()


def safe_timestamp_conversion(dt: datetime) -> int:
    """
    FIXED: Safely convert datetime to timestamp handling timezone awareness
    """
    if dt is None:
        return int(datetime.now(timezone.utc).timestamp())
    
    # If already timezone-aware, use directly
    if dt.tzinfo is not None:
        return int(dt.timestamp())
    
    # If naive, assume UTC
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def _mt5_df_from_rates(rates) -> pd.DataFrame:
    """
    Convert MT5 rates list/array to pandas DataFrame with UTC timestamp index.
    Optionally includes extended data (real_volume, spread) if available.
    """
    if rates is None or len(rates) == 0:
        logger.warning("No rates data provided to _mt5_df_from_rates")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'tick_volume']).set_index(pd.DatetimeIndex([], tz='UTC', name='time'))
    
    df = pd.DataFrame(list(rates))
    
    # Debug: log available columns
    logger.debug(f"MT5 data columns: {df.columns.tolist()}")
    
    if "time" not in df.columns:
        logger.error("MT5 data missing 'time' column")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'tick_volume']).set_index(pd.DatetimeIndex([], tz='UTC', name='time'))
    
    # Convert time to datetime with UTC timezone
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    
    # Build list of columns to keep (excluding 'time' which will be the index)
    cols_to_keep = []
    
    # Core OHLCV columns (required)
    for col in ['open', 'high', 'low', 'close', 'tick_volume']:
        if col in df.columns:
            cols_to_keep.append(col)
        else:
            logger.error(f"Missing required column: {col}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'tick_volume']).set_index(pd.DatetimeIndex([], tz='UTC', name='time'))
    
    # Optional extended columns
    if FETCH_EXTENDED_DATA:
        if "real_volume" in df.columns:
            cols_to_keep.append("real_volume")
            logger.debug("Including real_volume data")
        if "spread" in df.columns:
            cols_to_keep.append("spread")
            logger.debug("Including spread data")
    
    # Set time as index and select only relevant columns
    df = df.set_index("time")
    df = df[cols_to_keep]
    
    logger.debug(f"Processed DataFrame shape: {df.shape}, columns: {df.columns.tolist()}")
    
    return df


# Yahoo Finance symbol mapping removed — MT5-only


# ----------------------------
# DataManager class - FIXED
# ----------------------------
class DataManager:
    def __init__(
        self,
        mt5_login: int = MT5_LOGIN,
        mt5_password: str = MT5_PASSWORD,
        mt5_server: str = MT5_SERVER,
        mt5_path: Optional[str] = MT5_PATH,
        use_mt5: bool = True,
        cache_enabled: bool = True,
        max_retries: int = 3
    ):
        self.mt5_login = mt5_login
        self.mt5_password = mt5_password
        self.mt5_server = mt5_server
        self.mt5_path = mt5_path
        self._connected = False
        self.use_mt5 = use_mt5 and MT5_AVAILABLE
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        
        # Cache for broker-specific symbol names (to avoid repeated lookups)
        self._symbol_cache = {}
        
        if self.use_mt5 and not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available. MT5 disabled automatically.")
            self.use_mt5 = False
        
        logger.info(f"DataManager initialized: MT5={self.use_mt5}")

    # ----------------------------
    # Connection management
    # ----------------------------
    def connect(self) -> bool:
        """
        Connect to MT5 with provided credentials.
        Returns True if connected successfully.
        """
        import time as time_module
        start_time = time_module.time()

        # Validate prerequisites
        if not self.use_mt5:
            logger.info("MT5 usage disabled or MetaTrader5 module missing.")
            return False

        if self._connected:
            connection_logger.info("[STEP 3] Already connected to MT5")
            log_connection("Already connected to MT5")
            return True

        if not MT5_AVAILABLE or mt5 is None:
            connection_logger.error("[STEP 2] MT5 module not available - cannot connect")
            logger.error("MT5 module not available - cannot connect")
            log_error("MT5 not available", "MetaTrader5 module not installed. Run: pip install MetaTrader5")
            return False

        # Guard: MT5 Python API works only on Windows
        if os.name != "nt":
            connection_logger.error("[STEP 2] Unsupported OS for MT5 (requires Windows)")
            logger.error("MT5 is only supported on Windows. Current OS is not Windows.")
            log_error("MT5 unsupported OS", "MetaTrader 5 Python API requires Windows (win32)")
            self._connected = False
            return False

        connection_logger.info("="*80)
        connection_logger.info("CONNECTION ATTEMPT STARTED")
        connection_logger.info("="*80)
        connection_logger.debug(f"[STEP 1] Checking if MT5 usage is enabled: use_mt5={self.use_mt5}")
        connection_logger.debug(f"[STEP 1] ✓ MT5 usage is enabled (elapsed: {time_module.time()-start_time:.3f}s)")
        log_connection("Attempting to connect to MT5...", f"Server: {self.mt5_server}")

        # Step 4: Initialize MT5 with timeout and attach-first behavior
        connection_logger.info(f"[STEP 4] Starting MT5 initialization...")
        connection_logger.debug(f"[STEP 4] MT5 path: {self.mt5_path}")
        connection_logger.debug(f"[STEP 4] Path exists: {os.path.exists(self.mt5_path) if self.mt5_path else 'N/A'}")

        try:
            init_start = time_module.time()

            def _init_auto():
                return mt5.initialize()

            def _init_with_path():
                return mt5.initialize(self.mt5_path)

            initialized = False
            tried_methods = []

            def _try_init(callable_fn, label: str) -> bool:
                nonlocal tried_methods
                tried_methods.append(label)
                connection_logger.debug(f"[STEP 4] >>> Attempt: {label} (timeout {MT5_INIT_TIMEOUT_MS}ms) <<<")
                completed, result, err = _call_with_timeout(
                    callable_fn,
                    timeout_seconds=max(1, MT5_INIT_TIMEOUT_MS / 1000.0),
                )
                if not completed:
                    connection_logger.error(f"[STEP 4] {label} timed out after {MT5_INIT_TIMEOUT_MS}ms")
                    return False
                if err:
                    connection_logger.error(f"[STEP 4] {label} raised: {err}")
                    return False
                connection_logger.debug(f"[STEP 4] <<< {label} returned: {result} (took {time_module.time()-init_start:.3f}s) >>>")
                return bool(result)

            # Prefer attach-first (auto) to avoid launching terminal if already running
            if MT5_ATTACH_FIRST:
                initialized = _try_init(_init_auto, "mt5.initialize() attach-first")
                if not initialized and self.mt5_path and os.path.exists(self.mt5_path):
                    initialized = _try_init(_init_with_path, "mt5.initialize(path)")
            else:
                if self.mt5_path and os.path.exists(self.mt5_path):
                    initialized = _try_init(_init_with_path, "mt5.initialize(path)")
                if not initialized:
                    initialized = _try_init(_init_auto, "mt5.initialize() attach-first")

            connection_logger.info(f"[STEP 4] MT5 initialization result: {initialized} (attempts: {', '.join(tried_methods)})")

            if not initialized:
                error_info = mt5.last_error() if hasattr(mt5, 'last_error') else None
                connection_logger.error(f"[STEP 4] MT5 initialization failed. last_error={error_info}")
                error_msg = f"{error_info}" if error_info else "Unknown error"
                logger.error(f"MT5 initialize failed: {error_msg}")
                log_error(
                    "MT5 initialization failed",
                    f"{error_msg}\n\nTroubleshooting:\n1. Ensure MT5 is running and logged in\n2. Verify MT5_PATH if provided\n3. Close any modal dialogs in MT5 (e.g., update prompts)\n4. Try setting MT5_ATTACH_FIRST=0 to force path init",
                )
                self._connected = False
                return False

            connection_logger.info(f"[STEP 4] ✓ MT5 initialized successfully (elapsed: {time_module.time()-start_time:.3f}s)")

        except Exception as e:
            connection_logger.exception(f"[STEP 4] EXCEPTION during MT5 initialization: {e}")
            logger.exception(f"Failed to initialize MT5 terminal: {e}")
            log_error(
                "MT5 terminal initialization exception",
                f"{str(e)}\n\nThis usually means:\n1. MT5 terminal is not running\n2. MT5 path is incorrect\n3. MT5 needs to be restarted",
            )
            self._connected = False
            return False

        # Step 5: Login to MT5
        connection_logger.info(f"[STEP 5] Starting MT5 login...")
        connection_logger.debug(f"[STEP 5] Server: {self.mt5_server}")
        connection_logger.debug(f"[STEP 5] Login: {self.mt5_login}")
        connection_logger.debug(f"[STEP 5] Password: {'*' * len(self.mt5_password) if self.mt5_password else 'None'}")
        
        try:
            login_start = time_module.time()
            logger.info(f"Attempting login to {self.mt5_server} with account {self.mt5_login}")
            connection_logger.debug(f"[STEP 5] >>> About to call mt5.login() with timeout {MT5_LOGIN_TIMEOUT_MS}ms <<<")

            def _login_call():
                return mt5.login(login=self.mt5_login, password=self.mt5_password, server=self.mt5_server)

            completed, authorized, err = _call_with_timeout(
                _login_call,
                timeout_seconds=max(1, MT5_LOGIN_TIMEOUT_MS / 1000.0),
            )
            if not completed:
                connection_logger.error(f"[STEP 5] mt5.login() timed out after {MT5_LOGIN_TIMEOUT_MS}ms")
                authorized = False
            if err:
                connection_logger.error(f"[STEP 5] mt5.login() raised: {err}")
                authorized = False

            connection_logger.debug(f"[STEP 5] <<< mt5.login() returned: {authorized} (took {time_module.time()-login_start:.3f}s) >>>")
            connection_logger.info(f"[STEP 5] MT5 login result: {authorized} (elapsed: {time_module.time()-start_time:.3f}s)")
            
            if not authorized:
                error = mt5.last_error()
                connection_logger.error(f"Login failed: {error}")
                logger.error(f"MT5 login failed: {error}")
                log_error("MT5 login failed",
                         f"Error: {error}\n\nVerify:\n"
                         f"• Account: {self.mt5_login}\n"
                         f"• Server: {self.mt5_server}\n"
                         "• Password is correct\n"
                         "• Account is active and not expired")
                
                # Cleanup
                try:
                    mt5.shutdown()
                except:
                    pass
                return False
            
            # Connection successful
            self._connected = True
            connection_logger.info("="*80)
            connection_logger.info("CONNECTION SUCCESSFUL")
            connection_logger.info(f"Server: {self.mt5_server} | Account: {self.mt5_login}")
            connection_logger.info("="*80)
            logger.info(f"Connected to MT5: {self.mt5_server} (account {self.mt5_login})")
            log_success("Connected to MT5", f"Server: {self.mt5_server}, Account: {self.mt5_login}")
            return True
            
        except Exception as e:
            connection_logger.exception(f"Connection exception: {e}")
            logger.exception(f"MT5 connection failed: {e}")
            log_error("MT5 connection exception",
                     f"Unexpected error: {str(e)}\n\n"
                     "This typically indicates:\n"
                     "• MT5 terminal is not running\n"
                     "• Installation issue with MetaTrader5 package\n"
                     "• System compatibility problem")
            self._connected = False
            
            # Cleanup
            try:
                mt5.shutdown()
            except:
                pass
            return False

    def disconnect(self):
        """Disconnect from MT5"""
        if not self._connected:
            return
            
        try:
            if self.use_mt5 and MT5_AVAILABLE:
                mt5.shutdown()
                logger.info("Disconnected from MT5")
                log_connection("Disconnected from MT5")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
        finally:
            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self._connected

    def find_broker_symbol(self, standard_symbol: str) -> Optional[str]:
        """
        Find the broker-specific symbol name from a standard symbol name.
        Uses SYMBOL_VARIATIONS to check for common variations.
        Caches results to avoid repeated MT5 queries.
        
        Args:
            standard_symbol: Standard symbol name (e.g., "GBPUSD")
            
        Returns:
            Broker-specific symbol name if found, None otherwise
        """
        if not self.use_mt5 or not self._connected:
            return None
        
        # Normalize the input
        standard_symbol = normalize_symbol(standard_symbol)
        
        # Check cache first
        if standard_symbol in self._symbol_cache:
            cached = self._symbol_cache[standard_symbol]
            logger.debug(f"Using cached symbol mapping: {standard_symbol} -> {cached}")
            return cached
        
        # Get variations to try
        variations = SYMBOL_VARIATIONS.get(standard_symbol, [standard_symbol])
        
        logger.info(f"Searching for {standard_symbol} in MT5 (trying {len(variations)} variations)...")
        
        # Try each variation
        for variant in variations:
            try:
                symbol_info = mt5.symbol_info(variant)
                if symbol_info is not None:
                    logger.info(f"✅ Found broker symbol: {standard_symbol} -> {variant}")
                    self._symbol_cache[standard_symbol] = variant
                    return variant
            except Exception as e:
                logger.debug(f"Error checking variant {variant}: {e}")
                continue
        
        # If no exact match found, try fuzzy search
        logger.warning(f"No exact match found for {standard_symbol}, trying fuzzy search...")
        try:
            all_symbols = mt5.symbols_get()
            if all_symbols:
                # Look for symbols containing the standard name
                matches = [s.name for s in all_symbols if standard_symbol in s.name.upper()]
                if matches:
                    best_match = matches[0]
                    logger.info(f"💡 Fuzzy match found: {standard_symbol} -> {best_match}")
                    logger.info(f"   Other matches: {', '.join(matches[:5])}")
                    self._symbol_cache[standard_symbol] = best_match
                    return best_match
        except Exception as e:
            logger.error(f"Error during fuzzy symbol search: {e}")
        
        logger.error(f"❌ Could not find broker symbol for {standard_symbol}")
        logger.error(f"   Tried variations: {', '.join(variations)}")
        
        # Log available symbols for troubleshooting
        try:
            all_symbols = mt5.symbols_get()
            if all_symbols and len(all_symbols) > 0:
                logger.info(f"📋 Broker has {len(all_symbols)} symbols available")
                # Show first few symbols as examples
                sample_symbols = [s.name for s in all_symbols[:10]]
                logger.info(f"   Sample symbols: {', '.join(sample_symbols)}")
                logger.info(f"   TIP: Run 'python list_mt5_symbols.py' to see all available symbols")
        except Exception as e:
            logger.debug(f"Could not list available symbols: {e}")
        
        return None

    # ----------------------------
    # FIXED: Core fetch routines
    # ----------------------------
    def _fetch_mt5_ohlcv(self, symbol: str, timeframe: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
        """
        FIXED: Fetch OHLCV using MT5 copy_rates_range with improved timezone handling
        """
        if not self.use_mt5 or not self._connected:
            log_error("MT5 fetch failed - not connected")
            raise RuntimeError("MT5 usage disabled or not connected")

        tf_const = MT5_TF_MAP.get(timeframe.upper())
        if tf_const is None:
            log_error(f"Unsupported timeframe: {timeframe}")
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # FIXED: Normalize symbol consistently
        standard_symbol = normalize_symbol(symbol)
        
        log_data_fetch(f"Fetching {standard_symbol} {timeframe} from MT5")
        
        # FIXED: Auto-discover broker-specific symbol name
        broker_symbol = self.find_broker_symbol(standard_symbol)
        if broker_symbol is None:
            log_error(f"Symbol {standard_symbol} not found in MT5")
            raise ValueError(f"Symbol {standard_symbol} not found in MT5 broker symbols")
        
        # Use the broker-specific symbol name
        symbol = broker_symbol
        
        # Verify symbol exists
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found in MT5")

        # FIXED: Safe timestamp conversion
        utc_from = safe_timestamp_conversion(start_utc)
        utc_to = safe_timestamp_conversion(end_utc)

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                rates = mt5.copy_rates_range(symbol, tf_const, utc_from, utc_to)
                
                if rates is None or len(rates) == 0:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"No rates returned for {symbol} {timeframe} (attempt {attempt + 1})")
                        log_warning(f"Retry {attempt + 1}/{self.max_retries} for {symbol} {timeframe}")
                        time.sleep(1)
                        continue
                    else:
                        logger.warning(f"No rates returned for {symbol} {timeframe} after {self.max_retries} attempts")
                        log_error(f"No data returned for {symbol} {timeframe} after {self.max_retries} attempts")
                        return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
                
                df = _mt5_df_from_rates(rates)
                logger.info(f"Fetched {len(df)} bars for {symbol} {timeframe} from MT5")
                log_success(f"Fetched {len(df)} bars for {symbol} {timeframe} from MT5")
                return df
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"MT5 fetch failed for {symbol} {timeframe} (attempt {attempt + 1}): {e}")
                    time.sleep(2)
                else:
                    logger.error(f"MT5 fetch failed for {symbol} {timeframe} after {self.max_retries} attempts: {e}")
                    raise

        return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))

    # Yahoo Finance fetch removed — MT5-only

    def _load_from_cache(self, cache_path: str, start_utc: datetime, end_utc: datetime) -> Optional[pd.DataFrame]:
        """FIXED: Load data from cache with improved validation"""
        if not self.cache_enabled or not os.path.exists(cache_path):
            return None
            
        try:
            # FIXED: Read CSV without parse_dates to handle missing column errors
            df_cache = pd.read_csv(cache_path)
            
            # FIXED: Handle timezone properly and parse dates manually
            if 'time' not in df_cache.columns:
                logger.warning(f"Cache file missing 'time' column: {cache_path}")
                return None
            
            # Parse time column manually
            df_cache['time'] = pd.to_datetime(df_cache['time'])
            df_cache = df_cache.set_index('time')
            
            # Ensure timezone awareness
            if df_cache.index.tz is None:
                df_cache.index = pd.to_datetime(df_cache.index).tz_localize("UTC")
            else:
                df_cache.index = pd.to_datetime(df_cache.index).tz_convert("UTC")
            
            # Check if cache covers our requested range
            cache_start = df_cache.index.min()
            cache_end = df_cache.index.max()
            
            # Allow some tolerance (1 day)
            if cache_start <= start_utc and cache_end >= end_utc - timedelta(days=1):
                logger.info(f"Loaded from cache: {cache_path} ({len(df_cache)} bars)")
                return df_cache
            else:
                logger.info(f"Cache outdated: {cache_path}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to read cache {cache_path}: {e}")
            return None

    def _save_to_cache(self, df: pd.DataFrame, cache_path: str):
        """FIXED: Save DataFrame to cache with proper timezone handling"""
        if not self.cache_enabled or df.empty:
            return
            
        try:
            df_to_save = df.copy()
            
            # FIXED: Handle timezone-aware index properly
            df_to_save = df_to_save.reset_index()
            
            if 'time' in df_to_save.columns:
                # Convert to UTC and make timezone-naive for CSV storage
                if df_to_save['time'].dt.tz is not None:
                    df_to_save['time'] = df_to_save['time'].dt.tz_convert("UTC").dt.tz_localize(None)
                else:
                    df_to_save['time'] = pd.to_datetime(df_to_save['time'])
            
            df_to_save.to_csv(cache_path, index=False)
            logger.debug(f"Saved to cache: {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache data to {cache_path}: {e}")

    def fetch_ohlcv_for_timeframe(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int = 30,
        end_utc: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        FIXED: Public method to fetch OHLCV for a single timeframe (MT5-only).
        """
        # FIXED: Ensure end_utc is timezone-aware
        if end_utc is None:
            end_utc = datetime.now(timezone.utc)
        elif end_utc.tzinfo is None:
            end_utc = end_utc.replace(tzinfo=timezone.utc)
        
        start_utc = end_utc - timedelta(days=lookback_days)
        
        # FIXED: Normalize symbol
        symbol = normalize_symbol(symbol)
        
        logger.info(f"Fetching {symbol} {timeframe} for {lookback_days} days")

        # Try cache first
        cache_path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
        cached_df = self._load_from_cache(cache_path, start_utc, end_utc)
        if cached_df is not None and not cached_df.empty:
            return cached_df

        df = pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
        
        # Try MT5 if enabled and connected
        if self.use_mt5 and self._connected:
            try:
                logger.info(f"Fetching {symbol} {timeframe} from MT5...")
                df = self._fetch_mt5_ohlcv(symbol, timeframe, start_utc, end_utc)
                if not df.empty:
                    logger.info(f"✅ Successfully fetched {len(df)} bars from MT5")
            except Exception as e:
                logger.warning(f"MT5 fetch failed for {symbol} {timeframe}: {e}")
        elif self.use_mt5 and not self._connected:
            logger.warning(f"MT5 not connected - skipping MT5 data fetch. Call connect() first.")

        # FIXED: Final fallback - create synthetic data only if allowed
        if df.empty:
            allow_synth_env = os.getenv("ALLOW_SYNTHETIC_DATA", "1").strip().lower()
            allow_synth = allow_synth_env in ("1", "true", "yes", "on")
            if allow_synth:
                logger.warning(f"⚠️ All data sources failed for {symbol}. Creating synthetic data for testing.")
                df = self._create_synthetic_data(start_utc, end_utc, timeframe)
            else:
                logger.error(
                    f"❌ All data sources failed for {symbol} {timeframe}:"
                    f"\n  - MT5: {'Not available' if not self.use_mt5 else ('Not connected' if not self._connected else 'Failed')}"
                    f"\n  - Synthetic data: Disabled (ALLOW_SYNTHETIC_DATA={allow_synth_env})"
                )
            
        # FIXED: Clean and validate data
        if not df.empty:
            df = self._clean_dataframe(df)
            
            # FIXED: Validate we have enough data
            if len(df) < 50:
                logger.warning(f"Insufficient data for {symbol} {timeframe}: only {len(df)} bars")
            
            self._save_to_cache(df, cache_path)
        else:
            logger.error(f"No data available for {symbol} {timeframe}")

        return df

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """FIXED: Clean and validate DataFrame with improved checks"""
        if df.empty:
            return df
            
        # Remove rows with NaN in critical columns
        critical_cols = ['open', 'high', 'low', 'close']
        available_critical = [col for col in critical_cols if col in df.columns]
        
        initial_len = len(df)
        df = df.dropna(subset=available_critical)
        
        if len(df) < initial_len:
            logger.warning(f"Removed {initial_len - len(df)} rows with NaN values")
        
        # Ensure numeric types
        numeric_cols = ['open', 'high', 'low', 'close', 'tick_volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # FIXED: Validate OHLC relationships
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # High should be >= Open, Low, Close
            invalid_highs = (df['high'] < df[['open', 'low', 'close']].max(axis=1))
            # Low should be <= Open, High, Close
            invalid_lows = (df['low'] > df[['open', 'high', 'close']].min(axis=1))
            
            invalid_count = invalid_highs.sum() + invalid_lows.sum()
            if invalid_count > 0:
                logger.warning(f"Found {invalid_count} candles with invalid OHLC relationships")
                # Fix invalid relationships
                df['high'] = df[['open', 'high', 'close']].max(axis=1)
                df['low'] = df[['open', 'low', 'close']].min(axis=1)
                
        # Remove duplicates and sort index
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index()
        
        return df

    def _create_synthetic_data(self, start_utc: datetime, end_utc: datetime, timeframe: str) -> pd.DataFrame:
        """Create synthetic data for testing when no real data is available"""
        logger.warning("Creating synthetic data for testing purposes only!")
        
        # Determine frequency based on timeframe
        freq_map = {
            "D1": "D", "H4": "4H", "H1": "H", "M15": "15min", 
            "M5": "5min", "M1": "1min"
        }
        freq = freq_map.get(timeframe.upper(), "H")
        
        # Create date range
        dates = pd.date_range(start=start_utc, end=end_utc, freq=freq, tz='UTC')
        
        if len(dates) == 0:
            dates = pd.date_range(start=start_utc, end=start_utc + timedelta(hours=1), freq=freq, tz='UTC')
        
        # Create synthetic price data
        np.random.seed(42)  # For reproducible results
        n = len(dates)
        base_price = 1.2000
        returns = np.random.normal(0, 0.001, n)
        prices = base_price * (1 + np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.0001, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0005, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0005, n))),
            'close': prices,
            'tick_volume': np.random.randint(1000, 10000, n)
        }, index=dates)
        
        # Ensure high >= open, high >= close, low <= open, low <= close
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        logger.info(f"Created {len(df)} synthetic bars")
        return df

    def get_symbol_data(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        lookback_days: int = 60,
    ) -> Dict[str, pd.DataFrame]:
        """
        FIXED: Main convenience method with enhanced error handling per symbol.
        Returns a dict of DataFrames keyed by timeframe strings.
        """
        if timeframes is None:
            timeframes = ["D1", "H4", "H1"]

        # FIXED: Normalize symbol at entry point
        symbol = normalize_symbol(symbol)
        end_utc = datetime.now(timezone.utc)
        results = {}
        
        logger.info(f"Fetching data for {symbol} across {len(timeframes)} timeframes")
        
        for tf in timeframes:
            try:
                logger.info(f"Fetching {symbol} {tf} (last {lookback_days} days)")
                df = self.fetch_ohlcv_for_timeframe(
                    symbol, tf,
                    lookback_days=lookback_days,
                    end_utc=end_utc,
                )
                
                if not df.empty:
                    results[tf] = df
                    logger.info(f"✅ {symbol} {tf}: {len(df)} bars")
                else:
                    logger.warning(f"⚠️ No data for {symbol} {tf}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol} {tf}: {e}")
                # FIXED: Continue with other timeframes even if one fails

        if not results:
            logger.error(f"❌ No data obtained for {symbol} across any timeframe")
            
        return results

    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from MT5"""
        if not self.use_mt5 or not self._connected:
            return list(DEFAULT_SYMBOLS)
            
        try:
            symbols = mt5.symbols_get()
            return [s.name for s in symbols] if symbols else []
        except Exception as e:
            logger.error(f"Failed to get MT5 symbols: {e}")
            return list(DEFAULT_SYMBOLS)


# ----------------------------
# Example usage (main)
# ----------------------------
if __name__ == "__main__":
    # Demo of how to use this DataManager
    dm = DataManager()
    
    try:
        # Test with different symbols
        test_symbols = ["GBPUSD", "XAUUSD"]
        
        for symbol in test_symbols:
            print(f"\n{'='*50}")
            print(f"Testing {symbol}")
            print(f"{'='*50}")
            
            try:
                data = dm.get_symbol_data(
                    symbol, 
                    timeframes=["D1", "H4"], 
                    lookback_days=90,
                    
                )
                
                for tf, df in data.items():
                    if not df.empty:
                        print(f"✅ {symbol} {tf}: {len(df)} bars")
                        print(f"   Date range: {df.index.min()} to {df.index.max()}")
                        print(f"   Last close: {df['close'].iloc[-1]:.5f}")
                    else:
                        print(f"❌ {symbol} {tf}: No data")
                        
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                
    finally:
        dm.disconnect()

        print("\n✅ DataManager test completed")
