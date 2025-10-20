#!/bin/bash

# Launch script for Streamlit Trading Bot Dashboard
# Usage: ./launch_streamlit_gui.sh

echo "=========================================="
echo "🤖 Trading Bot Dashboard - Streamlit GUI"
echo "=========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed!"
    echo "📦 Installing streamlit..."
    pip install streamlit
    echo ""
fi

echo "🚀 Starting Streamlit Dashboard..."
echo "📍 Access the dashboard at: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Launch streamlit
streamlit run gui.py
