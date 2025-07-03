import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Config")

# Validate critical configuration
try:
    # MT5 Account Credentials
    MT5_ACCOUNT = int(os.getenv('MT5_ACCOUNT', 0))
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER = os.getenv('MT5_SERVER', '')
    
    # Trading Symbols and Timeframes
    SYMBOLS = ["XAUUSD", "BTCUSD", "US30", "USDJPY", "GBPJPY", "EURGBP", 
               "ETHUSD", "USOIL", "AUDJPY", "XAGUSD", "EURUSD", "GBPUSD"]
    TIMEFRAMES = [5, 15, 30]  # M5, M15, M30
    
    # Risk Management
    RISK_PER_TRADE = 50
    RISK_REWARD_RATIO = 5
    STOP_LOSS_ATR_FACTOR = 1.5
    TRAILING_STOP_ATR_FACTOR = 1.0
    ORDER_EXPIRATION_BARS = 5
    MIN_LOT_SIZE = 0.01
    MAX_LOT_SIZE = 1.0
    MAX_ALLOWED_LOT_SIZE = 1.0  

    
    # Strategy Parameters
    MIN_MA_GAP = 0.6
    MA1_PERIOD = 360
    MA2_PERIOD = 20
    ATR1_PERIOD = 10
    ATR2_PERIOD = 20
    RSI_PERIOD = 20
    
    # Trading Settings
    ENABLE_BUY = True
    ENABLE_SELL = True
    MAX_TRADES_PER_SYMBOL_TF = 1
    MAX_GLOBAL_TRADES = 15
    MIN_BARS_BETWEEN_TRADES = 5
    LIMIT_ORDER_DISTANCE = 2.0  # Pips
    
    # Session Settings (Lagos Time = GMT+1)
    ENABLE_SESSION = True
    SUNDAY_OPEN_HOUR = 22
    SUNDAY_OPEN_MIN = 15
    DAILY_CLOSE_HOUR = 21
    DAILY_CLOSE_MIN = 45
    
    # Prop Firm Protections (percentage-based)
    DAILY_LOSS_PERCENT = 5.0
    MAX_DRAWDOWN_PERCENT = 10.0
    MAX_SPREAD_MULTIPLIER = 3.0
    
    # Trade Journal
    ENABLE_TRADE_JOURNAL = True
    JOURNAL_FILENAME = "TradeJournal.csv"
    
    # Symbol-specific settings
    SYMBOL_SETTINGS = {
        "XAUUSD": {"slFactor": 2.0, "minMaGap": 0.6, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0, "pointMultiplier": 1.0},
        "BTCUSD": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 75, "rsiLower": 25, "trailingFactor": 1.0},
        "US30": {"slFactor": 1.5, "minMaGap": 0.8, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "USDJPY": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "GBPJPY": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "EURGBP": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "ETHUSD": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 75, "rsiLower": 25, "trailingFactor": 1.0, "pointMultiplier": 1.0},
        "USOIL": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 2.0},
        "AUDJPY": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "XAGUSD": {"slFactor": 2.0, "minMaGap": 0.6, "atr1Period": 10, "atr2Period": 20, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "EURUSD": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0},
        "GBPUSD": {"slFactor": 1.5, "minMaGap": 0.6, "atr1Period": 8, "atr2Period": 14, "rsiUpper": 70, "rsiLower": 30, "trailingFactor": 1.0}
    }
    
    BASE_MAGIC = 10000
    
    # Validate critical settings
    if not MT5_ACCOUNT or not MT5_PASSWORD or not MT5_SERVER:
        logger.error("MT5 credentials not configured in .env file")
        raise ValueError("Missing MT5 credentials")
        
    if not SYMBOLS or not TIMEFRAMES:
        logger.error("No symbols or timeframes configured")
        raise ValueError("Invalid symbol/timeframe configuration")
        
    logger.info("Configuration validated successfully")
    
except Exception as e:
    logger.exception(f"Configuration error: {e}")
    raise