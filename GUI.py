"""
GUI.py - Modern Trading Sentiment Analysis GUI
A comprehensive graphical interface for the trading sentiment analysis system.

Features:
- Run sentiment analysis on multiple symbols
- View and manage market data
- Verify predictions and accuracy
- Auto-retrain model based on performance
- Generate and view reports
- Configure system settings
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, List, Optional
import json

# Import system modules
try:
    from data_manager import DataManager, normalize_symbol
    from structure_analyzer import StructureAnalyzer
    from sentiment_engine import SentimentEngine
    from dashboard import Dashboard
    from verifier import Verifier
    from auto_retrain import AutoRetrain
    from report_generator import ReportGenerator
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Please ensure all required modules are in the same directory.")
    sys.exit(1)


class TradingGUI:
    """Main GUI Application for Trading Sentiment Analysis"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Sentiment Analysis System")
        self.root.geometry("1200x800")
        
        # Initialize components (lazy loading)
        self.data_manager = None
        self.sentiment_engine = None
        self.dashboard = None
        self.verifier = None
        self.retrainer = None
        self.report_generator = None
        
        # Queue for thread-safe GUI updates
        self.message_queue = queue.Queue()
        
        # Configuration
        self.config = self.load_config()
        
        # Setup UI
        self.setup_ui()
        
        # Start message queue processor
        self.process_queue()
        
    def load_config(self) -> Dict:
        """Load or create default configuration"""
        config_file = "config/gui_config.json"
        default_config = {
            "symbols": ["GBPUSD", "XAUUSD", "EURUSD"],
            "timeframes": ["D1", "H4", "H1"],
            "lookback_days": 60,
            "auto_connect_mt5": False,
            "excel_file": "sentiment_log.xlsx",
            "weights_file": "config/rule_weights.json"
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Create config directory and save defaults
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return default_config
    
    def save_config(self):
        """Save current configuration"""
        config_file = "config/gui_config.json"
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.log_message("✅ Configuration saved")
        except Exception as e:
            self.log_message(f"❌ Error saving config: {e}")
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Trading Sentiment Analysis System", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_analysis_tab()
        self.create_data_tab()
        self.create_verification_tab()
        self.create_retrain_tab()
        self.create_reports_tab()
        self.create_config_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def create_analysis_tab(self):
        """Create the main analysis tab"""
        analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(analysis_frame, text="📊 Analysis")
        
        # Configure grid
        analysis_frame.columnconfigure(0, weight=1)
        analysis_frame.rowconfigure(2, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(analysis_frame, text="Analysis Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Symbol selection
        ttk.Label(control_frame, text="Symbols:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.symbols_entry = ttk.Entry(control_frame, width=40)
        self.symbols_entry.insert(0, ", ".join(self.config["symbols"]))
        self.symbols_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Timeframes
        ttk.Label(control_frame, text="Timeframes:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.timeframes_entry = ttk.Entry(control_frame, width=20)
        self.timeframes_entry.insert(0, ", ".join(self.config["timeframes"]))
        self.timeframes_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        control_frame.columnconfigure(1, weight=2)
        control_frame.columnconfigure(3, weight=1)
        
        # Lookback period
        ttk.Label(control_frame, text="Lookback Days:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.lookback_var = tk.IntVar(value=self.config["lookback_days"])
        lookback_spin = ttk.Spinbox(control_frame, from_=7, to=365, textvariable=self.lookback_var, width=10)
        lookback_spin.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(analysis_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.run_analysis_btn = ttk.Button(button_frame, text="▶ Run Analysis", 
                                          command=self.run_analysis, style='Accent.TButton')
        self.run_analysis_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_analysis_btn = ttk.Button(button_frame, text="⏹ Stop", 
                                           command=self.stop_analysis, state=tk.DISABLED)
        self.stop_analysis_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="🔄 Clear Log", 
                  command=lambda: self.analysis_log.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="💾 Save Log", 
                  command=self.save_analysis_log).pack(side=tk.LEFT)
        
        # Analysis log
        log_frame = ttk.LabelFrame(analysis_frame, text="Analysis Log", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.analysis_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                     height=20, font=('Courier', 9))
        self.analysis_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output
        self.analysis_log.tag_config("success", foreground="green")
        self.analysis_log.tag_config("error", foreground="red")
        self.analysis_log.tag_config("warning", foreground="orange")
        self.analysis_log.tag_config("info", foreground="blue")
    
    def create_data_tab(self):
        """Create the data management tab"""
        data_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(data_frame, text="📈 Data")
        
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(1, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(data_frame, text="Data Fetch Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Symbol:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.data_symbol_entry = ttk.Entry(control_frame, width=15)
        self.data_symbol_entry.insert(0, "GBPUSD")
        self.data_symbol_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(control_frame, text="Timeframe:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.data_tf_var = tk.StringVar(value="H4")
        tf_combo = ttk.Combobox(control_frame, textvariable=self.data_tf_var, 
                               values=["M1", "M5", "M15", "H1", "H4", "D1", "W1"], 
                               width=10, state="readonly")
        tf_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(control_frame, text="Days:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.data_days_var = tk.IntVar(value=30)
        ttk.Spinbox(control_frame, from_=7, to=365, textvariable=self.data_days_var, 
                   width=10).grid(row=0, column=5, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(control_frame, text="📥 Fetch Data", 
                  command=self.fetch_data).grid(row=0, column=6, padx=(10, 0))
        
        ttk.Button(control_frame, text="🔌 Connect MT5", 
                  command=self.connect_mt5).grid(row=0, column=7, padx=(5, 0))
        
        # Data display
        display_frame = ttk.LabelFrame(data_frame, text="Data View", padding="5")
        display_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        self.data_display = scrolledtext.ScrolledText(display_frame, wrap=tk.NONE, 
                                                     height=20, font=('Courier', 9))
        self.data_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_verification_tab(self):
        """Create the verification tab"""
        verify_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(verify_frame, text="✓ Verification")
        
        verify_frame.columnconfigure(0, weight=1)
        verify_frame.rowconfigure(1, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(verify_frame, text="Verification Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Excel File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.verify_file_var = tk.StringVar(value=self.config["excel_file"])
        ttk.Entry(control_frame, textvariable=self.verify_file_var, 
                 width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(control_frame, text="📂 Browse", 
                  command=self.browse_excel_file).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(control_frame, text="▶ Run Verification", 
                  command=self.run_verification).grid(row=0, column=3)
        
        ttk.Button(control_frame, text="📊 Show Accuracy", 
                  command=self.show_accuracy).grid(row=0, column=4, padx=(5, 0))
        
        control_frame.columnconfigure(1, weight=1)
        
        # Verification log
        log_frame = ttk.LabelFrame(verify_frame, text="Verification Results", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.verify_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                   height=20, font=('Courier', 9))
        self.verify_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_retrain_tab(self):
        """Create the retraining tab"""
        retrain_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(retrain_frame, text="🔄 Retrain")
        
        retrain_frame.columnconfigure(0, weight=1)
        retrain_frame.rowconfigure(1, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(retrain_frame, text="Retraining Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Accuracy Threshold:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.threshold_var = tk.DoubleVar(value=0.70)
        ttk.Spinbox(control_frame, from_=0.5, to=0.95, increment=0.05, 
                   textvariable=self.threshold_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(control_frame, text="Min Samples:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.min_samples_var = tk.IntVar(value=10)
        ttk.Spinbox(control_frame, from_=5, to=100, textvariable=self.min_samples_var, 
                   width=10).grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(control_frame, text="▶ Check Performance", 
                  command=self.check_retrain_status).grid(row=0, column=4, padx=(10, 5))
        
        ttk.Button(control_frame, text="🔄 Run Retrain", 
                  command=self.run_retrain).grid(row=0, column=5)
        
        # Retrain log
        log_frame = ttk.LabelFrame(retrain_frame, text="Retraining Log", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.retrain_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                    height=20, font=('Courier', 9))
        self.retrain_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_reports_tab(self):
        """Create the reports tab"""
        reports_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(reports_frame, text="📄 Reports")
        
        reports_frame.columnconfigure(0, weight=1)
        reports_frame.rowconfigure(1, weight=1)
        
        # Control panel
        control_frame = ttk.LabelFrame(reports_frame, text="Report Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Reports Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.reports_dir_var = tk.StringVar(value="reports")
        ttk.Entry(control_frame, textvariable=self.reports_dir_var, 
                 width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(control_frame, text="📂 Browse", 
                  command=self.browse_reports_dir).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Refresh List", 
                  command=self.refresh_reports_list).grid(row=0, column=3, padx=(0, 5))
        
        ttk.Button(control_frame, text="📂 Open Folder", 
                  command=self.open_reports_folder).grid(row=0, column=4)
        
        control_frame.columnconfigure(1, weight=1)
        
        # Reports list
        list_frame = ttk.LabelFrame(reports_frame, text="Available Reports", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview for reports
        columns = ("Filename", "Symbol", "Date", "Size")
        self.reports_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.reports_tree.heading("#0", text="Type")
        self.reports_tree.heading("Filename", text="Filename")
        self.reports_tree.heading("Symbol", text="Symbol")
        self.reports_tree.heading("Date", text="Date")
        self.reports_tree.heading("Size", text="Size")
        
        self.reports_tree.column("#0", width=80)
        self.reports_tree.column("Filename", width=300)
        self.reports_tree.column("Symbol", width=100)
        self.reports_tree.column("Date", width=150)
        self.reports_tree.column("Size", width=100)
        
        self.reports_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reports_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.reports_tree.configure(yscrollcommand=scrollbar.set)
        
        # Double-click to open report
        self.reports_tree.bind("<Double-1>", self.open_selected_report)
        
        # Load reports on startup
        self.root.after(500, self.refresh_reports_list)
    
    def create_config_tab(self):
        """Create the configuration tab"""
        config_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(config_frame, text="⚙ Settings")
        
        # MT5 Settings
        mt5_frame = ttk.LabelFrame(config_frame, text="MT5 Connection Settings", padding="10")
        mt5_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        mt5_frame.columnconfigure(1, weight=1)
        
        ttk.Label(mt5_frame, text="MT5 Login:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.mt5_login_entry = ttk.Entry(mt5_frame, width=20)
        self.mt5_login_entry.insert(0, "")
        self.mt5_login_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(mt5_frame, text="MT5 Password:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.mt5_password_entry = ttk.Entry(mt5_frame, show="*", width=20)
        self.mt5_password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(mt5_frame, text="MT5 Server:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.mt5_server_entry = ttk.Entry(mt5_frame, width=20)
        self.mt5_server_entry.insert(0, "Pepperstone-Demo")
        self.mt5_server_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        self.auto_connect_var = tk.BooleanVar(value=self.config.get("auto_connect_mt5", False))
        ttk.Checkbutton(mt5_frame, text="Auto-connect on startup", 
                       variable=self.auto_connect_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # File paths
        paths_frame = ttk.LabelFrame(config_frame, text="File Paths", padding="10")
        paths_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        paths_frame.columnconfigure(1, weight=1)
        
        ttk.Label(paths_frame, text="Excel Log:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.excel_path_var = tk.StringVar(value=self.config["excel_file"])
        ttk.Entry(paths_frame, textvariable=self.excel_path_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(paths_frame, text="Weights File:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.weights_path_var = tk.StringVar(value=self.config["weights_file"])
        ttk.Entry(paths_frame, textvariable=self.weights_path_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Default symbols
        symbols_frame = ttk.LabelFrame(config_frame, text="Default Symbols & Timeframes", padding="10")
        symbols_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        symbols_frame.columnconfigure(1, weight=1)
        
        ttk.Label(symbols_frame, text="Symbols:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.config_symbols_entry = ttk.Entry(symbols_frame)
        self.config_symbols_entry.insert(0, ", ".join(self.config["symbols"]))
        self.config_symbols_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(symbols_frame, text="Timeframes:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.config_tf_entry = ttk.Entry(symbols_frame)
        self.config_tf_entry.insert(0, ", ".join(self.config["timeframes"]))
        self.config_tf_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Save button
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="💾 Save Configuration", 
                  command=self.save_settings).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="🔄 Reset to Defaults", 
                  command=self.reset_settings).pack(side=tk.LEFT)
    
    # ==================== Analysis Functions ====================
    
    def run_analysis(self):
        """Run full sentiment analysis"""
        # Get symbols
        symbols_text = self.symbols_entry.get().strip()
        if not symbols_text:
            messagebox.showwarning("Input Required", "Please enter at least one symbol")
            return
        
        symbols = [s.strip() for s in symbols_text.split(",")]
        timeframes = [tf.strip() for tf in self.timeframes_entry.get().split(",")]
        lookback_days = self.lookback_var.get()
        
        # Disable button during analysis
        self.run_analysis_btn.config(state=tk.DISABLED)
        self.stop_analysis_btn.config(state=tk.NORMAL)
        self.status_var.set("Running analysis...")
        
        # Run in thread
        thread = threading.Thread(target=self._run_analysis_thread, 
                                 args=(symbols, timeframes, lookback_days))
        thread.daemon = True
        thread.start()
    
    def _run_analysis_thread(self, symbols, timeframes, lookback_days):
        """Thread worker for running analysis"""
        try:
            self.log_analysis("\n" + "="*60)
            self.log_analysis(f"🚀 Starting Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_analysis("="*60 + "\n")
            
            # Initialize dashboard if needed
            if self.dashboard is None:
                self.log_analysis("Initializing dashboard...")
                self.dashboard = Dashboard(symbols=symbols)
            else:
                self.dashboard.symbols = [normalize_symbol(s) for s in symbols]
            
            # Run analysis
            self.log_analysis(f"Analyzing: {', '.join(symbols)}")
            self.log_analysis(f"Timeframes: {', '.join(timeframes)}")
            self.log_analysis(f"Lookback: {lookback_days} days\n")
            
            results = self.dashboard.run_full_cycle()
            
            self.log_analysis("\n" + "="*60)
            self.log_analysis("✅ Analysis Complete!")
            self.log_analysis("="*60)
            
            self.message_queue.put(("status", "Analysis complete"))
            
        except Exception as e:
            self.log_analysis(f"\n❌ Error during analysis: {e}", "error")
            self.message_queue.put(("status", "Analysis failed"))
            
        finally:
            self.message_queue.put(("enable_analysis_button", None))
    
    def stop_analysis(self):
        """Stop running analysis"""
        # Note: This is a placeholder - proper thread stopping would require more complex logic
        messagebox.showinfo("Stop Analysis", "Analysis stopping is not yet implemented.\nPlease wait for current analysis to complete.")
    
    def log_analysis(self, message, tag=""):
        """Log message to analysis log"""
        def update():
            self.analysis_log.insert(tk.END, message + "\n", tag)
            self.analysis_log.see(tk.END)
        
        self.root.after(0, update)
    
    def save_analysis_log(self):
        """Save analysis log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.analysis_log.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    # ==================== Data Functions ====================
    
    def connect_mt5(self):
        """Connect to MT5"""
        def connect_thread():
            try:
                self.log_data("Connecting to MT5...")
                if self.data_manager is None:
                    self.data_manager = DataManager()
                
                if self.data_manager.connect():
                    self.log_data("✅ Connected to MT5 successfully")
                    self.message_queue.put(("status", "MT5 Connected"))
                else:
                    self.log_data("❌ Failed to connect to MT5")
                    self.message_queue.put(("status", "MT5 Connection Failed"))
                    
            except Exception as e:
                self.log_data(f"❌ Error connecting to MT5: {e}")
                self.message_queue.put(("status", "MT5 Connection Error"))
        
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()
    
    def fetch_data(self):
        """Fetch market data"""
        symbol = self.data_symbol_entry.get().strip()
        timeframe = self.data_tf_var.get()
        days = self.data_days_var.get()
        
        if not symbol:
            messagebox.showwarning("Input Required", "Please enter a symbol")
            return
        
        def fetch_thread():
            try:
                self.log_data(f"\n📥 Fetching {symbol} {timeframe} data ({days} days)...\n")
                
                if self.data_manager is None:
                    self.data_manager = DataManager()
                
                df = self.data_manager.fetch_ohlcv_for_timeframe(
                    symbol, timeframe, lookback_days=days
                )
                
                if df is not None and not df.empty:
                    self.log_data(f"✅ Fetched {len(df)} bars\n")
                    self.log_data(f"Date range: {df.index.min()} to {df.index.max()}\n")
                    self.log_data("\nData Preview:\n")
                    self.log_data(df.head(20).to_string())
                    self.log_data("\n\nData Statistics:\n")
                    self.log_data(df.describe().to_string())
                    self.message_queue.put(("status", f"Data fetched: {len(df)} bars"))
                else:
                    self.log_data("❌ No data fetched")
                    self.message_queue.put(("status", "No data fetched"))
                    
            except Exception as e:
                self.log_data(f"❌ Error fetching data: {e}")
                self.message_queue.put(("status", "Data fetch failed"))
        
        thread = threading.Thread(target=fetch_thread)
        thread.daemon = True
        thread.start()
    
    def log_data(self, message):
        """Log message to data display"""
        def update():
            self.data_display.insert(tk.END, message + "\n")
            self.data_display.see(tk.END)
        
        self.root.after(0, update)
    
    # ==================== Verification Functions ====================
    
    def browse_excel_file(self):
        """Browse for Excel file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.verify_file_var.set(filename)
    
    def run_verification(self):
        """Run verification on predictions"""
        excel_file = self.verify_file_var.get()
        
        if not os.path.exists(excel_file):
            messagebox.showwarning("File Not Found", f"Excel file not found: {excel_file}")
            return
        
        def verify_thread():
            try:
                self.log_verify("\n" + "="*60)
                self.log_verify(f"🔍 Running Verification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log_verify("="*60 + "\n")
                
                if self.verifier is None:
                    self.verifier = Verifier(excel_file=excel_file)
                
                self.log_verify(f"Excel file: {excel_file}\n")
                self.log_verify("Starting verification process...\n")
                
                # Run verification
                results = self.verifier.verify_all()
                
                self.log_verify("\n" + "="*60)
                self.log_verify("✅ Verification Complete!")
                self.log_verify("="*60)
                
                self.message_queue.put(("status", "Verification complete"))
                
            except Exception as e:
                self.log_verify(f"\n❌ Error during verification: {e}")
                self.message_queue.put(("status", "Verification failed"))
        
        thread = threading.Thread(target=verify_thread)
        thread.daemon = True
        thread.start()
    
    def show_accuracy(self):
        """Show accuracy statistics"""
        excel_file = self.verify_file_var.get()
        
        if not os.path.exists(excel_file):
            messagebox.showwarning("File Not Found", f"Excel file not found: {excel_file}")
            return
        
        try:
            import pandas as pd
            df = pd.read_excel(excel_file)
            
            if "Verified" in df.columns:
                verified_count = df["Verified"].astype(str).str.contains("True|False", case=False, na=False).sum()
                correct_count = df["Verified"].astype(str).str.contains("True", case=False, na=False).sum()
                
                if verified_count > 0:
                    accuracy = (correct_count / verified_count) * 100
                    
                    message = f"Total Predictions: {len(df)}\n"
                    message += f"Verified: {verified_count}\n"
                    message += f"Correct: {correct_count}\n"
                    message += f"Accuracy: {accuracy:.2f}%"
                    
                    messagebox.showinfo("Accuracy Statistics", message)
                else:
                    messagebox.showinfo("No Data", "No verified predictions found")
            else:
                messagebox.showinfo("No Data", "No verification column found in Excel file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compute accuracy: {e}")
    
    def log_verify(self, message):
        """Log message to verification log"""
        def update():
            self.verify_log.insert(tk.END, message + "\n")
            self.verify_log.see(tk.END)
        
        self.root.after(0, update)
    
    # ==================== Retrain Functions ====================
    
    def check_retrain_status(self):
        """Check if retraining is needed"""
        def check_thread():
            try:
                self.log_retrain("\n" + "="*60)
                self.log_retrain(f"📊 Checking Retrain Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log_retrain("="*60 + "\n")
                
                threshold = self.threshold_var.get()
                min_samples = self.min_samples_var.get()
                
                if self.retrainer is None:
                    self.retrainer = AutoRetrain(threshold=threshold, min_samples=min_samples)
                
                # Load history
                df = self.retrainer.load_history()
                accuracy = self.retrainer.compute_accuracy()
                
                self.log_retrain(f"\nCurrent Accuracy: {accuracy*100:.2f}%")
                self.log_retrain(f"Threshold: {threshold*100:.2f}%")
                self.log_retrain(f"Total Samples: {len(df)}")
                self.log_retrain(f"Minimum Required: {min_samples}\n")
                
                if accuracy < threshold and len(df) >= min_samples:
                    self.log_retrain("⚠️ RETRAINING RECOMMENDED")
                    self.log_retrain(f"Accuracy ({accuracy*100:.2f}%) is below threshold ({threshold*100:.2f}%)")
                else:
                    self.log_retrain("✅ PERFORMANCE ACCEPTABLE")
                    self.log_retrain("No retraining needed at this time")
                
                self.message_queue.put(("status", f"Accuracy: {accuracy*100:.2f}%"))
                
            except Exception as e:
                self.log_retrain(f"\n❌ Error checking status: {e}")
                self.message_queue.put(("status", "Status check failed"))
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
    def run_retrain(self):
        """Run model retraining"""
        def retrain_thread():
            try:
                self.log_retrain("\n" + "="*60)
                self.log_retrain(f"🔄 Starting Retrain - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log_retrain("="*60 + "\n")
                
                threshold = self.threshold_var.get()
                min_samples = self.min_samples_var.get()
                
                if self.retrainer is None:
                    self.retrainer = AutoRetrain(threshold=threshold, min_samples=min_samples)
                
                # Run retraining
                result = self.retrainer.run_cycle()
                
                self.log_retrain("\n" + "="*60)
                self.log_retrain("✅ Retraining Complete!")
                self.log_retrain("="*60)
                
                self.message_queue.put(("status", "Retraining complete"))
                
            except Exception as e:
                self.log_retrain(f"\n❌ Error during retraining: {e}")
                self.message_queue.put(("status", "Retraining failed"))
        
        thread = threading.Thread(target=retrain_thread)
        thread.daemon = True
        thread.start()
    
    def log_retrain(self, message):
        """Log message to retrain log"""
        def update():
            self.retrain_log.insert(tk.END, message + "\n")
            self.retrain_log.see(tk.END)
        
        self.root.after(0, update)
    
    # ==================== Reports Functions ====================
    
    def browse_reports_dir(self):
        """Browse for reports directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.reports_dir_var.set(directory)
            self.refresh_reports_list()
    
    def refresh_reports_list(self):
        """Refresh the list of available reports"""
        reports_dir = self.reports_dir_var.get()
        
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        if not os.path.exists(reports_dir):
            return
        
        try:
            files = os.listdir(reports_dir)
            
            for filename in sorted(files):
                filepath = os.path.join(reports_dir, filename)
                if os.path.isfile(filepath):
                    # Get file stats
                    stat = os.stat(filepath)
                    size = f"{stat.st_size / 1024:.1f} KB"
                    
                    # Parse filename for info
                    parts = filename.rsplit("_", 1)
                    if len(parts) == 2:
                        symbol = parts[0]
                        date_str = parts[1].replace(".pdf", "").replace(".txt", "")
                    else:
                        symbol = "Unknown"
                        date_str = "Unknown"
                    
                    # Determine file type
                    if filename.endswith(".pdf"):
                        file_type = "📄 PDF"
                    elif filename.endswith(".txt"):
                        file_type = "📝 TXT"
                    elif filename.endswith(".xlsx"):
                        file_type = "📊 Excel"
                    else:
                        file_type = "📁 File"
                    
                    self.reports_tree.insert("", tk.END, text=file_type, 
                                           values=(filename, symbol, date_str, size))
            
            self.log_message(f"Found {len(files)} files in {reports_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list reports: {e}")
    
    def open_selected_report(self, event):
        """Open selected report file"""
        selection = self.reports_tree.selection()
        if not selection:
            return
        
        item = self.reports_tree.item(selection[0])
        filename = item['values'][0]
        filepath = os.path.join(self.reports_dir_var.get(), filename)
        
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{filepath}"')
            elif platform.system() == 'Windows':
                os.startfile(filepath)
            else:  # Linux
                os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open report: {e}")
    
    def open_reports_folder(self):
        """Open reports folder in file explorer"""
        reports_dir = self.reports_dir_var.get()
        
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{reports_dir}"')
            elif platform.system() == 'Windows':
                os.startfile(reports_dir)
            else:  # Linux
                os.system(f'xdg-open "{reports_dir}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    # ==================== Config Functions ====================
    
    def save_settings(self):
        """Save configuration settings"""
        try:
            # Update config from UI
            self.config["symbols"] = [s.strip() for s in self.config_symbols_entry.get().split(",")]
            self.config["timeframes"] = [tf.strip() for tf in self.config_tf_entry.get().split(",")]
            self.config["excel_file"] = self.excel_path_var.get()
            self.config["weights_file"] = self.weights_path_var.get()
            self.config["auto_connect_mt5"] = self.auto_connect_var.get()
            
            # Also update main UI
            self.symbols_entry.delete(0, tk.END)
            self.symbols_entry.insert(0, ", ".join(self.config["symbols"]))
            
            self.timeframes_entry.delete(0, tk.END)
            self.timeframes_entry.insert(0, ", ".join(self.config["timeframes"]))
            
            # Save to file
            self.save_config()
            
            messagebox.showinfo("Success", "Settings saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            # Reset to default config
            default_config = {
                "symbols": ["GBPUSD", "XAUUSD", "EURUSD"],
                "timeframes": ["D1", "H4", "H1"],
                "lookback_days": 60,
                "auto_connect_mt5": False,
                "excel_file": "sentiment_log.xlsx",
                "weights_file": "config/rule_weights.json"
            }
            
            self.config = default_config
            
            # Update UI
            self.config_symbols_entry.delete(0, tk.END)
            self.config_symbols_entry.insert(0, ", ".join(default_config["symbols"]))
            
            self.config_tf_entry.delete(0, tk.END)
            self.config_tf_entry.insert(0, ", ".join(default_config["timeframes"]))
            
            self.excel_path_var.set(default_config["excel_file"])
            self.weights_path_var.set(default_config["weights_file"])
            self.auto_connect_var.set(default_config["auto_connect_mt5"])
            
            self.save_config()
            messagebox.showinfo("Success", "Settings reset to defaults")
    
    # ==================== Utility Functions ====================
    
    def log_message(self, message):
        """Generic logging function"""
        print(message)  # Also print to console
    
    def process_queue(self):
        """Process messages from worker threads"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_var.set(msg_data)
                elif msg_type == "enable_analysis_button":
                    self.run_analysis_btn.config(state=tk.NORMAL)
                    self.stop_analysis_btn.config(state=tk.DISABLED)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TradingGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
