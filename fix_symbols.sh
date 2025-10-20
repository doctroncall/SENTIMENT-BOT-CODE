#!/bin/bash

echo "========================================"
echo "  Symbol Fixer - Auto-discover MT5 Symbols"
echo "========================================"
echo ""
echo "This will connect to your MT5 broker and"
echo "automatically find the correct symbol names."
echo ""
read -p "Press Enter to continue..."

python3 fix_symbols.py

echo ""
echo "========================================"
echo "  Done!"
echo "========================================"
echo ""
read -p "Press Enter to exit..."
