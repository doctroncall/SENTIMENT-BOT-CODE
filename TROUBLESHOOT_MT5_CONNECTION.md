# MT5 Connection Troubleshooting Guide

## Problem: Connection Stuck on "Connecting"

If your MT5 connection gets stuck or fails, follow these steps:

### Quick Fixes (Try These First)

1. **Restart MT5 Terminal**
   ```
   1. Close MetaTrader 5 completely (check Task Manager to ensure it's closed)
   2. Wait 5-10 seconds
   3. Reopen MT5 and login manually
   4. Try connecting from the application again
   ```

2. **Check MT5 is Running and Logged In**
   - Open MetaTrader 5 desktop application
   - Make sure you're logged in with your credentials
   - You should see your account balance and charts

3. **Enable Algorithmic Trading**
   - In MT5: Tools → Options → Expert Advisors
   - Check "Allow automated trading"
   - Check "Allow DLL imports"
   - Click OK and restart MT5

### Verify Your Credentials

Check your environment variables or configuration:
- **Login**: 211744072 (or your account number)
- **Server**: ExnessKE-MT5Trial9 (or your broker's server)
- **Password**: Check it's correct

### Check MT5 Terminal Path

The default path is: `C:\Program Files\MetaTrader 5\terminal64.exe`

If MT5 is installed elsewhere, set the environment variable:
```cmd
set MT5_PATH=C:\YourPath\MetaTrader 5\terminal64.exe
```

### Run Diagnostics

Run the diagnostic script to identify the issue:
```cmd
python test_mt5_diagnostics.py
```

This will tell you:
- Is MT5 terminal running?
- Is MetaTrader5 Python module installed?
- Can it find the MT5 terminal?
- What's the exact error?

### Common Issues

#### Issue 1: "MT5 terminal does not appear to be running"
**Solution**: Start MetaTrader 5 and login before connecting

#### Issue 2: "MT5 initialization failed: (1, 'Terminal: Global initialization failed')"
**Solution**: 
- Close ALL instances of MT5
- Wait 10 seconds
- Start MT5 again
- Login manually
- Try connecting

#### Issue 3: "MT5 login failed: Invalid credentials"
**Solution**: 
- Double-check your login, password, and server name
- Try logging in manually in MT5 first
- Update credentials in your configuration

#### Issue 4: Connection worked before but now fails
**Solution**:
- MT5 may have updated - restart it
- Your credentials may have changed
- Server name may have changed
- Try manual login in MT5 first

### Advanced Troubleshooting

1. **Check Task Manager**
   - Press Ctrl+Shift+Esc
   - Look for "terminal64.exe" or "terminal.exe" process
   - If not running, start MT5

2. **Check MT5 Logs**
   - In MT5: File → Open Data Folder
   - Open "Logs" folder
   - Check recent log files for errors

3. **Reinstall Dependencies**
   ```cmd
   pip uninstall MetaTrader5
   pip install MetaTrader5
   ```

4. **Use Fallback Data Source**
   - The system can use Yahoo Finance if MT5 fails
   - This is automatic - just configure symbols

### Still Having Issues?

If none of the above work:

1. Check the Status Monitor in the GUI for detailed error messages
2. Look at the application logs for the exact error
3. Make sure your MT5 account is active and has API access enabled
4. Contact your broker to ensure API access is allowed

### Prevention Tips

- Keep MT5 running and logged in before starting the application
- Don't close MT5 while the application is running
- Restart MT5 if you haven't used it in a while
- Keep the MetaTrader5 Python package updated
