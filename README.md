# Mean Reversion Gap Strategy Trading Bot


[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MetaTrader5](https://img.shields.io/badge/MetaTrader-5-orange)](https://www.metatrader5.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A sophisticated algorithmic trading system designed for prop firm challenges, implementing mean reversion strategies with advanced risk management and multi-timeframe analysis on MetaTrader 5.

## Overview

The Mean Reversion Prop Firm EA is a professional-grade trading system that combines:
- Gap-based mean reversion strategy
- Multi-timeframe analysis (M5, M15, M30)
- 12 major forex pairs and commodities
- Advanced risk management with prop firm rules
- Real-time position management with trailing stops

The system is optimized for prop firm challenges with strict risk constraints and delivers consistent performance through robust technical analysis and disciplined trade execution.

## Key Features

- **Multi-Indicator Strategy**:
  - EMA (360-period and 20-period)
  - RSI (20-period)
  - ATR (fast and slow periods)
  - Volume-weighted spread analysis

- **Advanced Risk Management**:
  - $50 fixed risk per trade
  - 1:5 risk-reward ratio
  - Daily loss limit (5% of equity)
  - Maximum drawdown protection (10%)
  - Spread monitoring and filtering

- **Prop Firm Compliance**:
  - Trading session management (Sunday-Friday)
  - Lagos time (GMT+1) based schedule
  - Max global trades limit
  - Trade journaling for verification

- **Position Management**:
  - Multi-stage trailing stops
  - Commodity-specific trailing (XAUUSD, USOIL, XAGUSD)
  - Profit-locking mechanism
  - Order expiration system

## Installation

### Prerequisites
- Python 3.8+
- MetaTrader 5 desktop application
- Active MT5 brokerage account

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Xtley001/Mean-Reversion-Gap-Strategy-Trading-Bot.git

   cd Mean-Reversion-Gap-Strategy-Trading-Bot

   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file with your MT5 credentials:
   ```ini
   MT5_ACCOUNT=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=your_broker_server
   ```

## Configuration

All configuration parameters are set in `config.py`:

### Trading Settings
| Parameter | Default | Description |
|-----------|---------|-------------|
| `SYMBOLS` | `["XAUUSD", "BTCUSD", ...]` | List of trading symbols |
| `TIMEFRAMES` | `[5, 15, 30]` | Timeframes in minutes (M5, M15, M30) |
| `RISK_PER_TRADE` | `50` | Dollar risk per trade |
| `RISK_REWARD_RATIO` | `5` | Risk-reward ratio (1:5) |
| `MAX_GLOBAL_TRADES` | `15` | Maximum simultaneous trades |
| `MAX_TRADES_PER_SYMBOL_TF` | `1` | Max trades per symbol/timeframe |
| `MIN_BARS_BETWEEN_TRADES` | `5` | Minimum bars between trades |
| `LIMIT_ORDER_DISTANCE` | `2.0` | Limit order distance in pips |

### Strategy Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_MA_GAP` | `0.6` | Minimum EMA gap percentage |
| `MA1_PERIOD` | `360` | Slow EMA period |
| `MA2_PERIOD` | `20` | Fast EMA period |
| `ATR1_PERIOD` | `10` | Fast ATR period |
| `ATR2_PERIOD` | `20` | Slow ATR period |
| `RSI_PERIOD` | `20` | RSI period |

### Risk Management
| Parameter | Default | Description |
|-----------|---------|-------------|
| `DAILY_LOSS_PERCENT` | `5.0` | Max daily loss (%) |
| `MAX_DRAWDOWN_PERCENT` | `10.0` | Max account drawdown (%) |
| `MIN_LOT_SIZE` | `0.01` | Minimum trade size |
| `MAX_LOT_SIZE` | `1.0` | Maximum trade size |
| `MAX_ALLOWED_LOT_SIZE` | `1.0` | User-defined max lot size |
| `STOP_LOSS_ATR_FACTOR` | `1.5` | ATR multiplier for stop loss |
| `TRAILING_STOP_ATR_FACTOR` | `1.0` | ATR multiplier for trailing stop |

### Session Management
| Parameter | Default | Description |
|-----------|---------|-------------|
| `ENABLE_SESSION` | `True` | Enable trading sessions |
| `SUNDAY_OPEN_HOUR` | `22` | Sunday session start hour (Lagos) |
| `SUNDAY_OPEN_MIN` | `15` | Sunday session start minute |
| `DAILY_CLOSE_HOUR` | `21` | Daily close hour (Friday) |
| `DAILY_CLOSE_MIN` | `45` | Daily close minute |

## Usage

### Running the Trading Engine

```bash
python main.py
```

### Sample Output
```
2025-07-03 05:53:08,987 - Main - INFO - Starting Xtley 001 Gap Trading System
2025-07-03 05:53:08,987 - Main - INFO - Initializing trading engine
2025-07-03 05:53:17,086 - TradingEngine - INFO - New trading day: 2025-07-03
2025-07-03 05:53:18,741 - TradingEngine - INFO - SELL LIMIT placed on ETHUSD TF:15 Lots:0.85 Magic:16010
2025-07-03 05:53:19,367 - TradingEngine - INFO - SELL LIMIT placed on USOIL TF:15 Lots:0.43 Magic:17010
2025-07-03 05:53:21,096 - TradingEngine - INFO - BUY LIMIT placed on EURUSD TF:5 Lots:0.12 Magic:15000
```

### Trade Journal
Trades are logged to `TradeJournal.csv` with the following columns:
```
Time,Symbol,Type,Volume,Price,Profit,Comment,Magic,SL,TP
2025-07-03 05:53:18,ETHUSD,SELL,0.85,1850.32,0,Xtley 001 Gap EA,16010,1845.50,1875.25
```

## Logging and Output

The system provides detailed logging with different severity levels:
- **INFO**: System status, trade entries/exits
- **WARNING**: Risk limits approached, order failures
- **ERROR**: Connection issues, calculation errors

Logs are written to:
- Console output
- `trading_system.log` file
- `TradeJournal.csv` (trade-specific details)

## Contribution Guidelines

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a new feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

### Coding Standards
- Follow PEP 8 style guide
- Include docstrings for all functions
- Add comments for complex logic
- Write unit tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, bug reports, or feature requests:
- 📧 Email: olubelachristley"gmail.com
- 🐛 GitHub Issues: [Open an issue](https://github.com/yourusername/mean-reversion-prop-firm-ea/issues)

---

**Disclaimer**: This software is for educational purposes only. Trading financial markets involves significant risk and is not suitable for all investors. Past performance is not indicative of future results. The authors assume no liability for any trading losses incurred while using this software.
