#!/bin/bash
# ============================================================
# Trading Sentiment Analysis Bot - Unified Startup (Linux/Mac)
# This is THE entry point - run this to start everything
# ============================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "  TRADING SENTIMENT ANALYSIS BOT"
echo "========================================"
echo ""
echo "  Unified Startup Script"
echo "  Starting all components..."
echo ""
echo "========================================"
echo ""

# ==========================================
# 1. Check Python Installation
# ==========================================
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[X] FAILED: Python not found!${NC}"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  - macOS: brew install python3"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] Python found:${NC}"
python3 --version
echo ""

# ==========================================
# 2. Check Critical Files
# ==========================================
echo "[2/5] Checking bot files..."
if [ ! -f "gui.py" ]; then
    echo -e "${RED}[X] FAILED: gui.py not found!${NC}"
    echo "Please ensure you're in the correct directory."
    exit 1
fi

if [ ! -f "dashboard.py" ]; then
    echo -e "${RED}[X] FAILED: dashboard.py not found!${NC}"
    echo "Core bot files are missing."
    exit 1
fi

echo -e "${GREEN}[OK] Core files found${NC}"
echo ""

# ==========================================
# 3. Check Dependencies
# ==========================================
echo "[3/5] Checking dependencies..."

if ! python3 -c "import streamlit" &> /dev/null; then
    echo -e "${YELLOW}[!] Streamlit not found. Installing...${NC}"
    pip3 install streamlit
    if [ $? -ne 0 ]; then
        echo -e "${RED}[X] Failed to install Streamlit${NC}"
        exit 1
    fi
fi

if ! python3 -c "import pandas" &> /dev/null; then
    echo -e "${YELLOW}[!] Missing dependencies. Installing from requirements.txt...${NC}"
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    else
        pip3 install pandas openpyxl MetaTrader5 reportlab yfinance
    fi
fi

echo -e "${GREEN}[OK] Dependencies ready${NC}"
echo ""

# ==========================================
# 4. Check MT5 Connection (Optional)
# ==========================================
echo "[4/5] Checking MT5 status..."
if [ -n "$MT5_LOGIN" ]; then
    echo -e "${GREEN}[OK] MT5 credentials found in environment${NC}"
else
    echo -e "${YELLOW}[!] MT5 credentials not set (optional - can connect via GUI)${NC}"
fi
echo ""

# ==========================================
# 5. Launch Streamlit GUI
# ==========================================
echo "[5/5] Launching Trading Bot GUI..."
echo ""
echo "========================================"
echo "  BOT IS STARTING..."
echo "========================================"
echo ""
echo "The Streamlit GUI will open in your browser."
echo ""
echo "IMPORTANT:"
echo "- Do NOT close this terminal"
echo "- Use the GUI to control the bot"
echo "- To stop: Press Ctrl+C here"
echo ""
echo "========================================"
echo ""

# Launch Streamlit
streamlit run gui.py --server.headless false

# If streamlit exits
echo ""
echo "========================================"
echo "  BOT STOPPED"
echo "========================================"
echo ""
