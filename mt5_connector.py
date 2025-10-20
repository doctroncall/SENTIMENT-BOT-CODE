"""
mt5_connector.py - Production-Grade MT5 Connection Module
==========================================================

This module provides a professional, robust interface for connecting to and
interacting with MetaTrader 5 terminals. It implements industry best practices
including singleton pattern, connection pooling, comprehensive error handling,
retry logic, and proper resource management.

Features:
---------
- Singleton pattern for connection management
- Thread-safe connection handling
- Automatic reconnection with exponential backoff
- Timeout protection for hanging operations
- Comprehensive logging and monitoring
- Context manager support for resource management
- Health checks and connection validation
- Graceful error handling and recovery
- Environment-based configuration
- Symbol caching and normalization

Usage:
------
    from mt5_connector import MT5Connector
    
    # Get connector instance
    connector = MT5Connector.get_instance()
    
    # Connect
    if connector.connect():
        # Use connection
        symbols = connector.get_available_symbols()
        
        # Disconnect when done
        connector.disconnect()
    
    # Or use context manager (recommended)
    with MT5Connector.get_instance() as connector:
        if connector.is_connected():
            symbols = connector.get_available_symbols()

Author: Trading Bot Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Any
from contextlib import contextmanager
from enum import Enum

# Optional dependency - graceful fallback if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class MT5Config:
    """Configuration container for MT5 connection parameters"""
    
    def __init__(
        self,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        path: Optional[str] = None,
        timeout: int = 30000,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        enable_health_check: bool = True,
        health_check_interval: int = 300  # 5 minutes
    ):
        """
        Initialize MT5 configuration
        
        Args:
            login: MT5 account login number
            password: MT5 account password
            server: MT5 broker server name
            path: Full path to terminal64.exe
            timeout: Operation timeout in milliseconds
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay between retry attempts in seconds
            enable_health_check: Enable periodic connection health checks
            health_check_interval: Interval between health checks in seconds
        """
        self.login = login or int(os.getenv("MT5_LOGIN", "211744072"))
        self.password = password or os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z")
        self.server = server or os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
        self.path = path or os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")
        self.timeout = int(os.getenv("MT5_TIMEOUT_MS", str(timeout)))
        self.max_retries = int(os.getenv("MT5_MAX_RETRIES", str(max_retries)))
        self.retry_delay = float(os.getenv("MT5_RETRY_DELAY", str(retry_delay)))
        self.enable_health_check = os.getenv("MT5_HEALTH_CHECK", "1").strip() in ("1", "true", "yes")
        self.health_check_interval = int(os.getenv("MT5_HEALTH_CHECK_INTERVAL", str(health_check_interval)))
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate configuration parameters
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.login or self.login == 0:
            return False, "Invalid MT5 login number"
        
        if not self.password:
            return False, "MT5 password not provided"
        
        if not self.server:
            return False, "MT5 server not provided"
        
        if self.timeout < 1000 or self.timeout > 60000:
            return False, "Timeout must be between 1000ms and 60000ms"
        
        if self.max_retries < 0 or self.max_retries > 10:
            return False, "Max retries must be between 0 and 10"
        
        return True, None
    
    def __repr__(self) -> str:
        return (f"MT5Config(login={self.login}, server={self.server}, "
                f"timeout={self.timeout}ms, max_retries={self.max_retries})")


# ============================================================================
# CONNECTION STATE
# ============================================================================

class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class MT5ConnectionError(Exception):
    """Base exception for MT5 connection errors"""
    pass


class MT5InitializationError(MT5ConnectionError):
    """Raised when MT5 initialization fails"""
    pass


class MT5LoginError(MT5ConnectionError):
    """Raised when MT5 login fails"""
    pass


class MT5TimeoutError(MT5ConnectionError):
    """Raised when an MT5 operation times out"""
    pass


class MT5NotAvailableError(MT5ConnectionError):
    """Raised when MT5 module is not available"""
    pass


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _call_with_timeout(fn, timeout_seconds: float, *args, **kwargs) -> Tuple[bool, Any, Optional[Exception]]:
    """
    Execute a function with timeout protection using daemon thread
    
    Args:
        fn: Function to execute
        timeout_seconds: Timeout in seconds
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
    
    Returns:
        Tuple of (completed, result, error)
    """
    result_container = {"done": False, "result": None, "error": None}
    
    def runner():
        try:
            result_container["result"] = fn(*args, **kwargs)
        except Exception as exc:
            result_container["error"] = exc
        finally:
            result_container["done"] = True
    
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    
    if not result_container["done"]:
        return False, None, MT5TimeoutError(f"Operation timed out after {timeout_seconds:.1f}s")
    
    return True, result_container["result"], result_container["error"]


def normalize_symbol(symbol: str) -> str:
    """
    DEPRECATED: Use symbol_utils.normalize_symbol() instead.
    Kept for backward compatibility.
    
    Args:
        symbol: Raw symbol name
    
    Returns:
        Normalized symbol name (uppercase, no special chars)
    """
    # Import centralized version
    try:
        from symbol_utils import normalize_symbol as _normalize
        return _normalize(symbol)
    except ImportError:
        # Fallback if symbol_utils not available
        if not symbol:
            return ""
        return symbol.upper().replace("/", "").replace("_", "").replace(" ", "").strip()


# ============================================================================
# MAIN CONNECTOR CLASS
# ============================================================================

class MT5Connector:
    """
    Production-grade MetaTrader 5 connection manager (Singleton)
    
    This class provides a robust, thread-safe interface for managing MT5
    connections with automatic retry, health checking, and resource management.
    """
    
    _instance: Optional['MT5Connector'] = None
    _lock = threading.RLock()
    
    def __init__(self, config: Optional[MT5Config] = None):
        """
        Initialize MT5 connector (use get_instance() instead)
        
        Args:
            config: MT5 configuration object
        """
        if not MT5_AVAILABLE:
            raise MT5NotAvailableError(
                "MetaTrader5 module is not available. "
                "Install with: pip install MetaTrader5"
            )
        
        self.config = config or MT5Config()
        self._state = ConnectionState.DISCONNECTED
        self._connection_lock = threading.RLock()
        self._symbol_cache: Dict[str, str] = {}
        self._last_health_check: float = 0
        self._connection_time: Optional[float] = None
        self._connection_attempts: int = 0
        self._health_check_thread: Optional[threading.Thread] = None
        self._health_check_stop = threading.Event()
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.MT5Connector")
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Add file handler if not already present
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            log_file = os.path.join("logs", f"mt5_connector_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(file_handler)
        
        self.logger.info(f"MT5Connector initialized with config: {self.config}")
    
    @classmethod
    def get_instance(cls, config: Optional[MT5Config] = None) -> 'MT5Connector':
        """
        Get or create singleton instance (thread-safe)
        
        Args:
            config: Configuration to use (only for first call)
        
        Returns:
            MT5Connector singleton instance
        
        Note:
            If instance already exists, config parameter is IGNORED.
            All subsequent calls will return the same instance with the original config.
            Use reset_instance() first if you need to create with different config.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        else:
            # Warn if trying to use different config
            if config is not None:
                existing_config = cls._instance.config
                # Check if configs differ (basic check on key fields)
                if (config.login != existing_config.login or 
                    config.server != existing_config.server):
                    cls._instance.logger.warning(
                        f"MT5Connector singleton already exists with different config! "
                        f"Existing: login={existing_config.login}, server={existing_config.server}. "
                        f"Requested: login={config.login}, server={config.server}. "
                        f"Using existing config. Call reset_instance() first if you need different config."
                    )
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (mainly for testing)"""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.disconnect()
                except Exception:
                    pass
                cls._instance = None
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def connect(self, force_reconnect: bool = False) -> bool:
        """
        Establish connection to MT5 terminal
        
        Args:
            force_reconnect: Force reconnection even if already connected
        
        Returns:
            True if connection successful, False otherwise
        """
        with self._connection_lock:
            # Check if already connected
            if self._state == ConnectionState.CONNECTED and not force_reconnect:
                self.logger.info("Already connected to MT5")
                return True
            
            # Disconnect if forcing reconnection
            if force_reconnect and self._state == ConnectionState.CONNECTED:
                self.logger.info("Forcing reconnection...")
                self.disconnect()
            
            # Validate configuration
            is_valid, error_msg = self.config.validate()
            if not is_valid:
                self.logger.error(f"Invalid configuration: {error_msg}")
                self._state = ConnectionState.ERROR
                return False
            
            # Attempt connection with retry
            self._state = ConnectionState.CONNECTING
            self._connection_attempts = 0
            
            for attempt in range(self.config.max_retries):
                self._connection_attempts = attempt + 1
                self.logger.info(f"Connection attempt {self._connection_attempts}/{self.config.max_retries}")
                
                try:
                    # Step 1: Initialize MT5
                    if not self._initialize():
                        if attempt < self.config.max_retries - 1:
                            self.logger.warning(f"Initialization failed, retrying in {self.config.retry_delay}s...")
                            time.sleep(self.config.retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            self._state = ConnectionState.ERROR
                            return False
                    
                    # Step 2: Login
                    if not self._login():
                        if attempt < self.config.max_retries - 1:
                            self.logger.warning(f"Login failed, retrying in {self.config.retry_delay}s...")
                            time.sleep(self.config.retry_delay * (attempt + 1))
                            self._shutdown()
                            continue
                        else:
                            self._state = ConnectionState.ERROR
                            self._shutdown()
                            return False
                    
                    # Connection successful
                    self._state = ConnectionState.CONNECTED
                    self._connection_time = time.time()
                    self._last_health_check = time.time()
                    
                    # Start health check thread if enabled
                    if self.config.enable_health_check:
                        self._start_health_check()
                    
                    self.logger.info(
                        f"Successfully connected to MT5 "
                        f"(Server: {self.config.server}, Account: {self.config.login})"
                    )
                    
                    # Log account information
                    self._log_account_info()
                    
                    return True
                
                except Exception as e:
                    self.logger.exception(f"Connection error on attempt {attempt + 1}: {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay * (attempt + 1))
                        continue
            
            # All attempts failed
            self._state = ConnectionState.ERROR
            self.logger.error(f"Failed to connect after {self.config.max_retries} attempts")
            return False
    
    def _initialize(self) -> bool:
        """
        Initialize MT5 terminal connection
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.logger.debug("Initializing MT5 terminal...")
        
        try:
            # Prefer attach-first approach (connect to already running terminal)
            attach_first = os.getenv("MT5_ATTACH_FIRST", "1").strip() in ("1", "true", "yes")
            
            if attach_first:
                # Try connecting to running terminal first
                self.logger.debug("Attempting to attach to running MT5 terminal...")
                completed, result, error = _call_with_timeout(
                    mt5.initialize,
                    timeout_seconds=self.config.timeout / 1000.0
                )
                
                if not completed:
                    self.logger.warning("Attach timed out, trying with path...")
                elif error:
                    self.logger.warning(f"Attach failed: {error}, trying with path...")
                elif result:
                    self.logger.info("Successfully attached to running MT5 terminal")
                    return True
            
            # Try with explicit path
            if self.config.path and os.path.exists(self.config.path):
                self.logger.debug(f"Initializing with path: {self.config.path}")
                completed, result, error = _call_with_timeout(
                    mt5.initialize,
                    timeout_seconds=self.config.timeout / 1000.0,
                    path=self.config.path
                )
                
                if not completed:
                    self.logger.error("Initialization with path timed out")
                    return False
                
                if error:
                    self.logger.error(f"Initialization with path failed: {error}")
                    return False
                
                if result:
                    self.logger.info("Successfully initialized MT5 with path")
                    return True
            
            # Last resort: try simple initialize again
            if not attach_first:
                self.logger.debug("Attempting simple MT5 initialization...")
                completed, result, error = _call_with_timeout(
                    mt5.initialize,
                    timeout_seconds=self.config.timeout / 1000.0
                )
                
                if completed and not error and result:
                    self.logger.info("Successfully initialized MT5")
                    return True
            
            # All methods failed
            error_info = mt5.last_error() if hasattr(mt5, 'last_error') else None
            self.logger.error(f"MT5 initialization failed: {error_info}")
            return False
        
        except Exception as e:
            self.logger.exception(f"Exception during MT5 initialization: {e}")
            return False
    
    def _login(self) -> bool:
        """
        Login to MT5 account
        
        Returns:
            True if login successful, False otherwise
        """
        self.logger.debug(f"Logging in to MT5 account {self.config.login} on {self.config.server}...")
        
        try:
            completed, result, error = _call_with_timeout(
                mt5.login,
                timeout_seconds=self.config.timeout / 1000.0,
                login=self.config.login,
                password=self.config.password,
                server=self.config.server
            )
            
            if not completed:
                self.logger.error(f"Login timed out after {self.config.timeout}ms")
                return False
            
            if error:
                self.logger.error(f"Login raised exception: {error}")
                return False
            
            if not result:
                error_info = mt5.last_error() if hasattr(mt5, 'last_error') else None
                self.logger.error(f"Login failed: {error_info}")
                return False
            
            self.logger.info(f"Successfully logged in to account {self.config.login}")
            return True
        
        except Exception as e:
            self.logger.exception(f"Exception during MT5 login: {e}")
            return False
    
    def _shutdown(self):
        """Shutdown MT5 connection"""
        try:
            if MT5_AVAILABLE and mt5 is not None:
                mt5.shutdown()
                self.logger.debug("MT5 connection shutdown")
        except Exception as e:
            self.logger.warning(f"Error during shutdown: {e}")
    
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        with self._connection_lock:
            if self._state == ConnectionState.DISCONNECTED:
                self.logger.debug("Already disconnected")
                return
            
            # Stop health check thread
            if self._health_check_thread is not None:
                self._health_check_stop.set()
                self._health_check_thread.join(timeout=5)
                self._health_check_thread = None
            
            # Shutdown connection
            self._shutdown()
            
            # Update state
            self._state = ConnectionState.DISCONNECTED
            self._connection_time = None
            self._symbol_cache.clear()
            
            self.logger.info("Disconnected from MT5")
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to MT5
        
        Returns:
            True if connected, False otherwise
        """
        return self._state == ConnectionState.CONNECTED
    
    def get_state(self) -> ConnectionState:
        """
        Get current connection state
        
        Returns:
            Current ConnectionState
        """
        return self._state
    
    # ========================================================================
    # HEALTH CHECKS
    # ========================================================================
    
    def _start_health_check(self):
        """Start background health check thread"""
        if self._health_check_thread is not None and self._health_check_thread.is_alive():
            return
        
        self._health_check_stop.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="MT5HealthCheck"
        )
        self._health_check_thread.start()
        self.logger.debug("Health check thread started")
    
    def _health_check_loop(self):
        """Background health check loop"""
        while not self._health_check_stop.wait(self.config.health_check_interval):
            try:
                if self._state == ConnectionState.CONNECTED:
                    if not self.health_check():
                        self.logger.warning("Health check failed, attempting reconnection...")
                        self.connect(force_reconnect=True)
            except Exception as e:
                self.logger.exception(f"Error in health check loop: {e}")
    
    def health_check(self) -> bool:
        """
        Perform connection health check
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if self._state != ConnectionState.CONNECTED:
            return False
        
        try:
            # Try to get account info as health check
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.warning("Health check failed: account_info returned None")
                return False
            
            self._last_health_check = time.time()
            self.logger.debug("Health check passed")
            return True
        
        except Exception as e:
            self.logger.error(f"Health check failed with exception: {e}")
            return False
    
    # ========================================================================
    # SYMBOL MANAGEMENT
    # ========================================================================
    
    def get_available_symbols(self, group: str = "*") -> List[str]:
        """
        Get list of available symbols
        
        Args:
            group: Symbol group filter (default: all symbols)
        
        Returns:
            List of symbol names
        """
        if not self.is_connected():
            self.logger.warning("Cannot get symbols - not connected to MT5")
            return []
        
        try:
            symbols = mt5.symbols_get(group=group)
            if symbols is None:
                self.logger.warning("No symbols returned from MT5")
                return []
            
            symbol_names = [s.name for s in symbols]
            self.logger.debug(f"Retrieved {len(symbol_names)} symbols")
            return symbol_names
        
        except Exception as e:
            self.logger.error(f"Error getting symbols: {e}")
            return []
    
    def find_symbol(self, standard_symbol: str, variations: Optional[List[str]] = None) -> Optional[str]:
        """
        Find broker-specific symbol name from standard symbol
        
        Args:
            standard_symbol: Standard symbol name (e.g., "GBPUSD")
            variations: List of symbol variations to try (optional)
        
        Returns:
            Broker-specific symbol name if found, None otherwise
        """
        if not self.is_connected():
            self.logger.warning("Cannot find symbol - not connected to MT5")
            return None
        
        # Normalize input
        standard_symbol = normalize_symbol(standard_symbol)
        
        # Check cache
        if standard_symbol in self._symbol_cache:
            cached = self._symbol_cache[standard_symbol]
            self.logger.debug(f"Using cached symbol: {standard_symbol} -> {cached}")
            return cached
        
        # Default variations if not provided
        if variations is None:
            variations = [
                standard_symbol,
                f"{standard_symbol}m",
                f"{standard_symbol}.a",
                f"{standard_symbol}.",
                f"{standard_symbol}.raw"
            ]
        
        self.logger.debug(f"Searching for {standard_symbol} (trying {len(variations)} variations)")
        
        # Try each variation
        for variant in variations:
            try:
                symbol_info = mt5.symbol_info(variant)
                if symbol_info is not None:
                    self.logger.info(f"Found symbol: {standard_symbol} -> {variant}")
                    self._symbol_cache[standard_symbol] = variant
                    return variant
            except Exception as e:
                self.logger.debug(f"Error checking variant {variant}: {e}")
        
        # Try fuzzy search
        try:
            all_symbols = mt5.symbols_get()
            if all_symbols:
                matches = [s.name for s in all_symbols if standard_symbol in s.name.upper()]
                if matches:
                    best_match = matches[0]
                    self.logger.info(f"Fuzzy match found: {standard_symbol} -> {best_match}")
                    self._symbol_cache[standard_symbol] = best_match
                    return best_match
        except Exception as e:
            self.logger.error(f"Error in fuzzy symbol search: {e}")
        
        self.logger.warning(f"Could not find symbol: {standard_symbol}")
        return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Any]:
        """
        Get detailed information about a symbol
        
        Args:
            symbol: Symbol name
        
        Returns:
            SymbolInfo object or None if not found
        """
        if not self.is_connected():
            self.logger.warning("Cannot get symbol info - not connected to MT5")
            return None
        
        try:
            return mt5.symbol_info(symbol)
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    # ========================================================================
    # ACCOUNT INFORMATION
    # ========================================================================
    
    def get_account_info(self) -> Optional[Any]:
        """
        Get current account information
        
        Returns:
            AccountInfo object or None if not available
        """
        if not self.is_connected():
            self.logger.warning("Cannot get account info - not connected to MT5")
            return None
        
        try:
            return mt5.account_info()
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def _log_account_info(self):
        """Log account information"""
        try:
            account_info = self.get_account_info()
            if account_info:
                self.logger.info(f"Account Info: Login={account_info.login}, "
                               f"Server={account_info.server}, "
                               f"Balance={account_info.balance}, "
                               f"Leverage=1:{account_info.leverage}")
        except Exception as e:
            self.logger.debug(f"Could not log account info: {e}")
    
    # ========================================================================
    # DATA RETRIEVAL
    # ========================================================================
    
    def get_rates(self, symbol: str, timeframe: int, date_from: int, date_to: int) -> Optional[Any]:
        """
        Get historical rates for a symbol
        
        Args:
            symbol: Symbol name
            timeframe: MT5 timeframe constant
            date_from: Start timestamp (UTC)
            date_to: End timestamp (UTC)
        
        Returns:
            Array of rates or None if failed
        """
        if not self.is_connected():
            self.logger.warning("Cannot get rates - not connected to MT5")
            return None
        
        try:
            rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
            if rates is None or len(rates) == 0:
                self.logger.warning(f"No rates returned for {symbol}")
                return None
            
            self.logger.debug(f"Retrieved {len(rates)} rates for {symbol}")
            return rates
        
        except Exception as e:
            self.logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================
    
    def __enter__(self) -> 'MT5Connector':
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - does NOT disconnect (singleton pattern)"""
        # Note: We don't disconnect here because this is a singleton
        # Call disconnect() explicitly when you want to close the connection
        pass
    
    # ========================================================================
    # STATUS AND DIAGNOSTICS
    # ========================================================================
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics and diagnostics
        
        Returns:
            Dictionary with connection statistics
        """
        uptime = None
        if self._connection_time is not None:
            uptime = time.time() - self._connection_time
        
        return {
            "state": self._state.value,
            "connected": self.is_connected(),
            "connection_time": datetime.fromtimestamp(self._connection_time, tz=timezone.utc).isoformat() 
                              if self._connection_time else None,
            "uptime_seconds": uptime,
            "connection_attempts": self._connection_attempts,
            "last_health_check": datetime.fromtimestamp(self._last_health_check, tz=timezone.utc).isoformat()
                                if self._last_health_check > 0 else None,
            "cached_symbols": len(self._symbol_cache),
            "config": {
                "login": self.config.login,
                "server": self.config.server,
                "timeout_ms": self.config.timeout,
                "max_retries": self.config.max_retries
            }
        }
    
    def __repr__(self) -> str:
        return (f"MT5Connector(state={self._state.value}, "
                f"connected={self.is_connected()}, "
                f"server={self.config.server})")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

@contextmanager
def mt5_connection(config: Optional[MT5Config] = None):
    """
    Context manager for MT5 connection
    
    Usage:
        with mt5_connection() as connector:
            if connector.is_connected():
                symbols = connector.get_available_symbols()
    
    Args:
        config: Optional MT5 configuration
    
    Yields:
        MT5Connector instance
    """
    connector = MT5Connector.get_instance(config)
    try:
        connector.connect()
        yield connector
    finally:
        # Note: We don't disconnect here to preserve singleton pattern
        # Connection will be reused across multiple context managers
        pass


# ============================================================================
# MODULE LEVEL FUNCTIONS (for backward compatibility)
# ============================================================================

def get_connector(config: Optional[MT5Config] = None) -> MT5Connector:
    """
    Get MT5 connector instance (convenience function)
    
    Args:
        config: Optional MT5 configuration
    
    Returns:
        MT5Connector singleton instance
    """
    return MT5Connector.get_instance(config)


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    # Setup console logging for testing
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger(__name__)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    print("\n" + "="*80)
    print("MT5 Connector Test")
    print("="*80 + "\n")
    
    try:
        # Test singleton pattern
        print("1. Testing singleton pattern...")
        connector1 = MT5Connector.get_instance()
        connector2 = MT5Connector.get_instance()
        assert connector1 is connector2, "Singleton pattern failed!"
        print("✅ Singleton pattern working\n")
        
        # Test connection
        print("2. Testing connection...")
        if connector1.connect():
            print("✅ Connected successfully\n")
            
            # Test account info
            print("3. Testing account info...")
            account_info = connector1.get_account_info()
            if account_info:
                print(f"✅ Account: {account_info.login}")
                print(f"   Server: {account_info.server}")
                print(f"   Balance: {account_info.balance}\n")
            
            # Test symbol search
            print("4. Testing symbol search...")
            gbpusd = connector1.find_symbol("GBPUSD")
            if gbpusd:
                print(f"✅ Found GBPUSD: {gbpusd}\n")
            
            # Test symbol listing
            print("5. Testing symbol listing...")
            symbols = connector1.get_available_symbols()
            print(f"✅ Found {len(symbols)} symbols\n")
            
            # Test connection stats
            print("6. Connection statistics:")
            stats = connector1.get_connection_stats()
            print(f"   State: {stats['state']}")
            print(f"   Uptime: {stats['uptime_seconds']:.1f}s")
            print(f"   Cached symbols: {stats['cached_symbols']}\n")
            
            # Disconnect
            print("7. Disconnecting...")
            connector1.disconnect()
            print("✅ Disconnected\n")
        else:
            print("❌ Connection failed\n")
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80)
    print("Test completed")
    print("="*80 + "\n")
