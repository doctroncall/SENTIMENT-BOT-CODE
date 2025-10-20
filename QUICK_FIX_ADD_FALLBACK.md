# Quick Fix: Add Legacy Fallback

If you want to keep my fixes but add back the legacy fallback for safety:

## Option 1: Add Environment Variable to Force Legacy

Add this to your environment or at the top of data_manager.py:

```python
# Force legacy connection if connector fails
USE_LEGACY_FALLBACK = os.getenv("USE_LEGACY_FALLBACK", "1") == "1"
```

Then in `connect()` method, change:

```python
# CURRENT (no fallback):
if not MT5_CONNECTOR_AVAILABLE:
    logger.error("MT5Connector not available - cannot connect")
    return False

# TO (with fallback):
if not MT5_CONNECTOR_AVAILABLE:
    if USE_LEGACY_FALLBACK:
        logger.warning("MT5Connector not available, using legacy connection")
        return self._connect_legacy()  # Call legacy method
    else:
        logger.error("MT5Connector not available - cannot connect")
        return False
```

## Option 2: Just Rollback Everything

Run:
```bash
bash ROLLBACK_NOW.sh
```

This will revert to the working state before my changes.

## Option 3: Diagnose First

Run:
```bash
python DIAGNOSE_HANG.py
```

This will tell you exactly WHERE it's hanging and WHY.

---

## My Apologies

I'm sorry for breaking something that was working! I should have:
1. ✅ Asked you to test BEFORE removing fallback
2. ✅ Made changes incrementally
3. ✅ Kept legacy as backup

The analysis was correct (dual connection IS a problem), but the implementation was too aggressive - I removed the safety net.

---

## Recommended Next Steps

1. **FIRST**: Run `python DIAGNOSE_HANG.py` to see where it hangs
2. **THEN**: Decide:
   - If it's an MT5 terminal issue (dialog open, etc.) → Fix that
   - If it's my code → Run `bash ROLLBACK_NOW.sh`
3. **AFTER**: We can re-apply fixes more carefully with fallback intact
