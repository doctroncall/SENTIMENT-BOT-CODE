"""
Main Entry Point for SMC Trading Bot
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager
from logger_setup import setup_logging
from trading_bot import SMCTradingBot


def main():
    """Main entry point"""
    try:
        # Load configuration
        print("Loading configuration...")
        config_path = os.path.join(os.path.dirname(__file__), 'config_cursor_smc', 'config.yaml')
        config_manager = ConfigManager(config_path)
        config = config_manager.get()
        
        # Setup logging
        setup_logging(config['logging'])
        logger = logging.getLogger(__name__)
        
        logger.info("Starting SMC Trading Bot")
        logger.info(f"Symbols: {config['trading']['symbols']}")
        logger.info(f"Timeframe: {config['trading']['timeframe']}")
        logger.info(f"Max positions: {config['trading']['max_positions']}")
        
        # Create and run bot
        bot = SMCTradingBot(config)
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
