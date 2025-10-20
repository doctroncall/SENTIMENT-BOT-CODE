"""
symbol_utils.py - Centralized Symbol Utilities
================================================

Provides consistent symbol normalization across the entire codebase.
This ensures all modules handle symbol names identically.

Author: Trading Bot Team
Version: 1.0.0
"""


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol name for consistency across the system.
    
    This function provides a single source of truth for symbol normalization,
    ensuring consistent behavior across all modules (data_manager, verifier,
    mt5_connector, etc.).
    
    Normalization rules:
    - Convert to uppercase
    - Remove forward slashes (/)
    - Remove underscores (_)
    - Remove spaces
    - Strip leading/trailing whitespace
    
    Args:
        symbol: Raw symbol name (e.g., "GBP/USD", "GBP USD", "gbpusd")
    
    Returns:
        Normalized symbol name (e.g., "GBPUSD")
    
    Examples:
        >>> normalize_symbol("GBP/USD")
        'GBPUSD'
        >>> normalize_symbol("GBP USD")
        'GBPUSD'
        >>> normalize_symbol("gbpusd")
        'GBPUSD'
        >>> normalize_symbol("xau/usd")
        'XAUUSD'
        >>> normalize_symbol(" EUR_USD ")
        'EURUSD'
    """
    if not symbol:
        return ""
    
    # Apply all normalization rules
    normalized = symbol.upper()
    normalized = normalized.replace("/", "")
    normalized = normalized.replace("_", "")
    normalized = normalized.replace(" ", "")
    normalized = normalized.strip()
    
    return normalized


# Alias for backward compatibility
normalize = normalize_symbol


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("GBP/USD", "GBPUSD"),
        ("GBP USD", "GBPUSD"),
        ("gbpusd", "GBPUSD"),
        ("xau/usd", "XAUUSD"),
        (" EUR_USD ", "EURUSD"),
        ("BTCUSD", "BTCUSD"),
        ("", ""),
    ]
    
    print("Testing symbol normalization:")
    print("=" * 50)
    
    all_passed = True
    for input_sym, expected in test_cases:
        result = normalize_symbol(input_sym)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"{status} {repr(input_sym):20} → {repr(result):10} (expected {repr(expected)})")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
