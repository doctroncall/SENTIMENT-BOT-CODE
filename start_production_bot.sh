#!/bin/bash
#===============================================================================
# Production MT5 Trading Bot - Startup Script
#===============================================================================
# This script ensures all dependencies are installed and runs the bot with
# proper error handling and logging.
#
# Usage:
#   ./start_production_bot.sh [symbols]
#
# Examples:
#   ./start_production_bot.sh                    # Default symbols (GBPUSD,XAUUSD,EURUSD)
#   ./start_production_bot.sh GBPUSD,EURUSD      # Custom symbols
#===============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "================================================================================"
echo "               🤖 PRODUCTION MT5 TRADING BOT - STARTUP                        "
echo "================================================================================"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️ ${NC}$1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check Python installation
print_info "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_success "Python3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    print_success "Python found: $(python --version)"
else
    print_error "Python not found! Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_info "Python version: $PYTHON_VERSION"

# Check and install dependencies
print_info "Checking dependencies..."

if $PYTHON_CMD -c "import pandas" 2>/dev/null; then
    print_success "pandas installed"
else
    print_warning "pandas not installed. Installing..."
    $PYTHON_CMD -m pip install pandas numpy --quiet
    print_success "pandas installed"
fi

if $PYTHON_CMD -c "import numpy" 2>/dev/null; then
    print_success "numpy installed"
else
    print_warning "numpy not installed. Installing..."
    $PYTHON_CMD -m pip install numpy --quiet
    print_success "numpy installed"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p data logs reports
print_success "Directories ready"

# Check for run_bot.py
if [ ! -f "run_bot.py" ]; then
    print_error "run_bot.py not found in current directory!"
    exit 1
fi

print_success "All pre-flight checks passed!"

# Run the bot
echo ""
echo "================================================================================"
echo "                    🚀 STARTING BOT...                                        "
echo "================================================================================"
echo ""

# Parse command line arguments
SYMBOLS=${1:-"GBPUSD,XAUUSD,EURUSD"}

# Set environment variables for production
export PYTHONUNBUFFERED=1  # Disable Python output buffering
export MT5_TIMEOUT_MS=30000  # 30 second timeout for MT5 operations

# Run the bot with symbols
if [ -n "$SYMBOLS" ]; then
    print_info "Running bot with symbols: $SYMBOLS"
    $PYTHON_CMD run_bot.py "$SYMBOLS" 2>&1 | tee "logs/bot_run_$(date +%Y%m%d_%H%M%S).log"
else
    print_info "Running bot with default symbols"
    $PYTHON_CMD run_bot.py 2>&1 | tee "logs/bot_run_$(date +%Y%m%d_%H%M%S).log"
fi

BOT_EXIT_CODE=$?

echo ""
echo "================================================================================"

if [ $BOT_EXIT_CODE -eq 0 ]; then
    print_success "Bot completed successfully!"
    echo "================================================================================"
    exit 0
else
    print_error "Bot exited with error code: $BOT_EXIT_CODE"
    echo "================================================================================"
    exit $BOT_EXIT_CODE
fi
