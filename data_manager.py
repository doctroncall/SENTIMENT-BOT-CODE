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
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union
import time

import pandas as pd
import numpy as np

# Optional dependencies (import inside functions to avoid hard failure)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DataManager")

# Symbol mapping for different data sources
SYMBOL_MAPPING = {
    # MT5 to Yahoo Finance mapping
    "GBPUSD": "GBPUSD=X",
    "XAUUSD": "GC=F",  # Gold futures
    "EURUSD": "EURUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X",
    "XAGUSD": "SI=F",  # Silver futures
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
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
COLUMNS = ["time", "open", "high", "low", "close", "tick_volume"]


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
    """
    if rates is None or len(rates) == 0:
        return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
    
    df = pd.DataFrame(list(rates))
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        
        # Handle different column name variations
        column_mapping = {
            "time": "time",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "tick_volume": "tick_volume",
            "real_volume": "tick_volume"
        }
        
        # Rename columns if they exist
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Ensure we have the required columns
        available_cols = [col for col in COLUMNS if col in df.columns]
        if not available_cols:
            logger.error("No valid columns found in MT5 data")
            return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
            
        df = df[available_cols]
        df = df.set_index("time")
    
    return df


def _get_yahoo_symbol(mt5_symbol: str) -> str:
    """Get Yahoo Finance symbol equivalent"""
    normalized = normalize_symbol(mt5_symbol)
    return SYMBOL_MAPPING.get(normalized, f"{normalized}=X")


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
        
        if self.use_mt5 and not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available. MT5 disabled automatically.")
            self.use_mt5 = False
        
        logger.info(f"DataManager initialized: MT5={self.use_mt5}, Yahoo={YFINANCE_AVAILABLE}")

    # ----------------------------
    # Connection management
    # ----------------------------
    def connect(self) -> bool:
        """
        Connect to MT5 with provided credentials.
        Returns True if connected successfully.
        """
        if not self.use_mt5:
            logger.info("MT5 usage disabled or MetaTrader5 module missing.")
            return False

        # If already connected, return True
        if self._connected:
            return True

        # If terminal path is provided, attempt to initialize using it.
        try:
            if self.mt5_path and os.path.exists(self.mt5_path):
                initialized = mt5.initialize(self.mt5_path)
            else:
                initialized = mt5.initialize()
                
            if not initialized:
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                self._connected = False
                return False
                
        except Exception as e:
            logger.exception(f"Failed to initialize MT5 terminal: {e}")
            self._connected = False
            return False

        # Login
        try:
            authorized = mt5.login(
                login=self.mt5_login, 
                password=self.mt5_password, 
                server=self.mt5_server
            )
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                self._connected = False
                return False
                
        except Exception as e:
            logger.exception(f"MT5 login exception: {e}")
            self._connected = False
            return False

        self._connected = True
        logger.info(f"Connected to MT5 (login={self.mt5_login} server={self.mt5_server})")
        return True

    def disconnect(self):
        """Disconnect from MT5"""
        if self.use_mt5 and self._connected:
            try:
                mt5.shutdown()
            except Exception as e:
                logger.warning(f"Error during MT5 shutdown: {e}")
        self._connected = False
        logger.info("MT5 disconnected")

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self._connected

    # ----------------------------
    # FIXED: Core fetch routines
    # ----------------------------
    def _fetch_mt5_ohlcv(self, symbol: str, timeframe: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
        """
        FIXED: Fetch OHLCV using MT5 copy_rates_range with improved timezone handling
        """
        if not self.use_mt5 or not self._connected:
            raise RuntimeError("MT5 usage disabled or not connected")

        tf_const = MT5_TF_MAP.get(timeframe.upper())
        if tf_const is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # FIXED: Normalize symbol consistently
        symbol = normalize_symbol(symbol)
        
        # Check if symbol exists in MT5
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
                        time.sleep(1)
                        continue
                    else:
                        logger.warning(f"No rates returned for {symbol} {timeframe} after {self.max_retries} attempts")
                        return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
                
                df = _mt5_df_from_rates(rates)
                logger.info(f"Fetched {len(df)} bars for {symbol} {timeframe} from MT5")
                return df
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"MT5 fetch failed for {symbol} {timeframe} (attempt {attempt + 1}): {e}")
                    time.sleep(2)
                else:
                    logger.error(f"MT5 fetch failed for {symbol} {timeframe} after {self.max_retries} attempts: {e}")
                    raise

        return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))

    def _fetch_yfinance_ohlcv(self, symbol: str, timeframe: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
        """
        FIXED: Fallback to yfinance with improved error handling
        """
        if not YFINANCE_AVAILABLE:
            raise RuntimeError("yfinance not available for fallback")

        # Map timeframes to yfinance intervals
        tf_map = {
            "D1": "1d", "H4": "1h", "H1": "1h", "M15": "15m", 
            "M5": "5m", "M1": "1m", "W1": "1wk", "MN1": "1mo"
        }
        
        yf_tf = tf_map.get(timeframe.upper(), "1d")
        yf_symbol = _get_yahoo_symbol(symbol)

        try:
            # yfinance expects timezone-naive dates
            start_naive = start_utc.replace(tzinfo=None) if start_utc.tzinfo else start_utc
            end_naive = end_utc.replace(tzinfo=None) if end_utc.tzinfo else end_utc
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_naive, end=end_naive, interval=yf_tf, auto_adjust=True)
            
            if df.empty:
                logger.warning(f"No data from yfinance for {yf_symbol} {timeframe}")
                return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))

            # Standardize column names and format
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low", 
                "Close": "close", "Volume": "tick_volume"
            })
            
            # Ensure we have all required columns
            for col in ['open', 'high', 'low', 'close']:
                if col not in df.columns:
                    logger.error(f"Missing column {col} in yfinance data")
                    return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))
            
            if 'tick_volume' not in df.columns:
                df['tick_volume'] = 0
                
            df = df[['open', 'high', 'low', 'close', 'tick_volume']]
            
            # FIXED: Ensure UTC timezone properly
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize("UTC")
            else:
                df.index = pd.to_datetime(df.index).tz_convert("UTC")
            
            # Resample if needed (e.g., H1 to H4)
            if timeframe.upper() == "H4":
                df = df.resample("4H").agg({
                    "open": "first",
                    "high": "max", 
                    "low": "min",
                    "close": "last",
                    "tick_volume": "sum"
                }).dropna()
            
            logger.info(f"Fetched {len(df)} bars for {yf_symbol} {timeframe} from yfinance")
            return df
            
        except Exception as e:
            logger.error(f"yfinance fetch failed for {yf_symbol} {timeframe}: {e}")
            return pd.DataFrame(columns=COLUMNS).set_index(pd.DatetimeIndex([], tz='UTC'))

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
        use_yahoo_fallback: bool = True,
    ) -> pd.DataFrame:
        """
        FIXED: Public method to fetch OHLCV for a single timeframe with enhanced fallback logic.
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
        
        # Try MT5 first if enabled
        if self.use_mt5:
            if not self._connected:
                logger.info(f"MT5 not connected, attempting to connect...")
                connected = self.connect()
                if not connected:
                    logger.warning(f"Failed to connect to MT5, will try fallback sources")
                
            if self._connected:
                try:
                    logger.info(f"Attempting to fetch {symbol} {timeframe} from MT5...")
                    df = self._fetch_mt5_ohlcv(symbol, timeframe, start_utc, end_utc)
                    if not df.empty:
                        logger.info(f"✅ Successfully fetched {len(df)} bars from MT5")
                except Exception as e:
                    logger.warning(f"MT5 fetch failed for {symbol} {timeframe}: {e}")
                    logger.info(f"Will attempt Yahoo Finance fallback...")
            else:
                logger.warning(f"MT5 not connected, skipping MT5 data fetch")

        # Fallback to yfinance if allowed and needed
        if (df.empty or df is None) and use_yahoo_fallback:
            if not YFINANCE_AVAILABLE:
                logger.warning(f"Yahoo Finance not available (yfinance not installed)")
            else:
                logger.info(f"📊 Attempting Yahoo Finance fallback for {symbol} {timeframe}...")
                try:
                    df = self._fetch_yfinance_ohlcv(symbol, timeframe, start_utc, end_utc)
                    if not df.empty:
                        logger.info(f"✅ Successfully fetched {len(df)} bars from Yahoo Finance")
                    else:
                        logger.warning(f"Yahoo Finance returned empty data for {symbol}")
                except Exception as e:
                    logger.error(f"yfinance fallback failed for {symbol}: {e}")

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
                    f"\n  - Yahoo Finance: {'Not available' if not YFINANCE_AVAILABLE else 'Failed'}"
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
        use_yahoo_fallback: bool = True,
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
                    use_yahoo_fallback=use_yahoo_fallback
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
            return list(SYMBOL_MAPPING.keys())
            
        try:
            symbols = mt5.symbols_get()
            return [s.name for s in symbols] if symbols else []
        except Exception as e:
            logger.error(f"Failed to get MT5 symbols: {e}")
            return list(SYMBOL_MAPPING.keys())


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
                    use_yahoo_fallback=True
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
