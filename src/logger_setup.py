"""
Logging Setup
Configures application logging
"""

import logging
import logging.handlers
import os
from typing import Dict


def setup_logging(config: Dict):
    """
    Setup logging configuration
    
    Args:
        config: Logging configuration dictionary
    """
    # Create logs directory if it doesn't exist
    log_file = config.get('file', 'logs/smc_bot.log')
    log_dir = os.path.dirname(log_file)
    
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Get log level
    log_level_str = config.get('level', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        max_bytes = config.get('max_bytes', 10485760)  # 10MB
        backup_count = config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup message
    logging.info("=" * 60)
    logging.info("SMC Trading Bot - Logging initialized")
    logging.info(f"Log level: {log_level_str}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 60)
