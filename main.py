# main.py - Entry point for the Xtley 001 Gap Trading System

import logging
from engine import TradingEngine

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Main")

def main():
    logger.info("Starting Xtley 001 Gap Trading System")
    logger.info("Initializing trading engine")
    
    try:
        # Create and run the trading engine
        engine = TradingEngine()
        logger.info("Trading engine initialized successfully")
        
        # Start the main trading loop
        engine.run()
    except Exception as e:
        logger.exception("Fatal error in trading system")
    finally:
        logger.info("Trading system shutdown complete")

if __name__ == "__main__":
    main()