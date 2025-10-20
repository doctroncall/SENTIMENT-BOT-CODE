#!/bin/bash

echo "========================================"
echo "  List All MT5 Symbols"
echo "========================================"
echo ""
echo "This will show all available symbols"
echo "in your MT5 broker account."
echo ""
read -p "Press Enter to continue..."

python3 list_mt5_symbols.py --all

echo ""
echo "========================================"
echo "  Done!"
echo "========================================"
echo ""
read -p "Press Enter to exit..."
