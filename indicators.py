import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config import logger

class Indicators:
    @staticmethod
    def get_data(symbol, timeframe, count):
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {symbol} TF:{timeframe}")
                return None
            return pd.DataFrame(rates)
        except Exception as e:
            logger.error(f"Error getting data for {symbol} TF:{timeframe}: {e}")
            return None
    
    @staticmethod
    def sma(data, period):
        return data['close'].rolling(period).mean()
    
    @staticmethod
    def ema(data, period):
        return data['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def atr(data, period):
        try:
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return tr.rolling(period).mean()
        except Exception as e:
            logger.error(f"ATR calculation error: {e}")
            return pd.Series(np.zeros(len(data)))
    
    @staticmethod
    def rsi(data, period):
        try:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return pd.Series(np.zeros(len(data)))
    
    @staticmethod
    def get_indicators(symbol, timeframe, ma1_period, ma2_period, atr1_period, atr2_period, rsi_period):
        try:
            # Get enough bars for the longest indicator
            count = max(ma1_period, ma2_period, atr1_period, atr2_period, rsi_period) + 100
            
            data = Indicators.get_data(symbol, timeframe, count)
            if data is None or data.empty:
                return None
            
            # Calculate indicators
            ma_fast = Indicators.ema(data, ma1_period)
            ma_slow = Indicators.ema(data, ma2_period)
            atr_fast = Indicators.atr(data, atr1_period)
            atr_slow = Indicators.atr(data, atr2_period)
            rsi = Indicators.rsi(data, rsi_period)
            
            # Return last 3 values for each indicator
            return {
                'ma_fast': ma_fast.iloc[-3:].values,
                'ma_slow': ma_slow.iloc[-3:].values,
                'atr_fast': atr_fast.iloc[-3:].values,
                'atr_slow': atr_slow.iloc[-3:].values,
                'rsi': rsi.iloc[-3:].values,
                'close': data['close'].iloc[-1]  # Current close price
            }
        except Exception as e:
            logger.error(f"Indicator error for {symbol} TF:{timeframe}: {e}")
            return None
    
    @staticmethod
    def get_spread(symbol):
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                return symbol_info.spread * symbol_info.point
            return 0
        except Exception as e:
            logger.error(f"Spread error for {symbol}: {e}")
            return 0
    
    @staticmethod
    def get_avg_spread(symbol, period=50):
        try:
            spreads = []
            for _ in range(period):
                spread = Indicators.get_spread(symbol)
                if spread > 0:
                    spreads.append(spread)
            return sum(spreads) / len(spreads) if spreads else 0
        except Exception as e:
            logger.error(f"Avg spread error for {symbol}: {e}")
            return 0