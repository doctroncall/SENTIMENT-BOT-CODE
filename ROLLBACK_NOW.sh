#!/bin/bash
# EMERGENCY ROLLBACK SCRIPT
# This will revert to the previous working state

echo "🔄 Rolling back to previous working commit..."
echo ""

# Show current commit
echo "Current commit:"
git log --oneline -1
echo ""

# Rollback these specific commits
echo "Rolling back changes..."
git revert --no-commit a723b29 404017e

echo ""
echo "✅ Rollback complete!"
echo ""
echo "Files reverted to working state:"
echo "  - data_manager.py"
echo "  - verifier.py"
echo "  - GUI.py"
echo ""
echo "To commit the rollback:"
echo "  git commit -m 'Rollback MT5 connection changes'"
echo ""
echo "Or to undo this rollback:"
echo "  git revert --abort"
