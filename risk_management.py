import MetaTrader5 as mt5
import logging
from config import *

logger = logging.getLogger("RiskManager")

class RiskManager:
    @staticmethod
    def calculate_dollar_risk_per_point(symbol):
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger.warning(f"No symbol info for {symbol}")
                return 0
                
            # Get symbol-specific point multiplier
            settings = SYMBOL_SETTINGS.get(symbol, {})
            point_multiplier = settings.get('pointMultiplier', 1.0)
            
            # Special handling for cryptocurrencies
            if symbol in ["BTCUSD", "ETHUSD"]:
                # Cryptos typically have point = 1.0
                return 1.0 * point_multiplier
                
            contract_size = symbol_info.trade_contract_size
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            point = symbol_info.point
            
            if tick_size == 0 or point == 0:
                logger.warning(f"Invalid tick/point for {symbol}")
                return 0
                
            return (tick_value * point) / tick_size * point_multiplier
        except Exception as e:
            logger.error(f"Dollar risk error for {symbol}: {e}")
            return 0

    @staticmethod
    def calculate_lot_size(symbol, entry, sl, risk_amount):
        try:
            if entry == 0 or sl == 0 or entry == sl:
                return 0
                
            risk_points = abs(entry - sl)
            dollar_per_point = RiskManager.calculate_dollar_risk_per_point(symbol)
            if dollar_per_point == 0:
                return 0
                
            symbol_info = mt5.symbol_info(symbol)
            contract_size = symbol_info.trade_contract_size if symbol_info else 1
            
            value_per_point_per_lot = dollar_per_point * contract_size
            risk_per_lot = risk_points * value_per_point_per_lot
            
            if risk_per_lot <= 0:
                return 0
                
            lots = risk_amount / risk_per_lot
            
            # Apply min/max limits
            min_lot = MIN_LOT_SIZE
            max_lot = min(MAX_LOT_SIZE, MAX_ALLOWED_LOT_SIZE)  # Respect both limits
            
            if lots < min_lot:
                lots = min_lot
            elif lots > max_lot:
                lots = max_lot
            
            # Normalize to step size
            step = symbol_info.volume_step if symbol_info else 0.01
            if step > 0:
                lots = step * round(lots / step)
            
            return round(lots, 2)
        except Exception as e:
            logger.error(f"Lot size error for {symbol}: {e}")
            return 0

    @staticmethod
    def adjust_risk_for_fixed_dollar(symbol, sl, tp, entry, lot, is_buy, atr_value):
        try:
            dollar_per_point = RiskManager.calculate_dollar_risk_per_point(symbol)
            if dollar_per_point == 0:
                return sl, tp
                
            symbol_info = mt5.symbol_info(symbol)
            contract_size = symbol_info.trade_contract_size if symbol_info else 1
            value_per_point_per_lot = dollar_per_point * contract_size
            risk_per_point = value_per_point_per_lot * lot
            
            if risk_per_point <= 0:
                return sl, tp
                
            # Calculate required risk points for $50 risk
            required_risk_points = RISK_PER_TRADE / risk_per_point
            point = symbol_info.point if symbol_info else 0.0001
            
            # Adjust SL first
            if is_buy:
                sl = entry - required_risk_points * point
                # Maintain risk/reward ratio
                sl_distance = entry - sl
                tp = entry + (sl_distance * RISK_REWARD_RATIO)
            else:
                sl = entry + required_risk_points * point
                sl_distance = sl - entry
                tp = entry - (sl_distance * RISK_REWARD_RATIO)
                
            return sl, tp
        except Exception as e:
            logger.error(f"Risk adjustment error for {symbol}: {e}")
            return sl, tp