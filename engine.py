import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import pytz
import os
import signal
import logging
from config import *
from indicators import Indicators
from risk_management import RiskManager

class PendingOrder:
    def __init__(self, ticket, symbol, timeframe, placement_time, placement_bar, magic):
        self.ticket = ticket
        self.symbol = symbol
        self.timeframe = timeframe
        self.placement_time = placement_time
        self.placement_bar = placement_bar
        self.magic = magic

class TradingEngine:
    def __init__(self):
        self.logger = logging.getLogger("TradingEngine")
        self.logger.info("Initializing trading engine")
        
        # Initialize running flag
        self.running = False
        
        # Verify credentials
        if not MT5_ACCOUNT or not MT5_PASSWORD or not MT5_SERVER:
            self.logger.error("MT5 credentials not configured")
            return
            
        # Initialize MT5 connection
        if not self.initialize_mt5():
            self.logger.error("MT5 initialization failed")
            return
        
        # Rest of initialization
        account_info = mt5.account_info()
        self.equity_high = account_info.equity if account_info else 10000
        self.equity_at_start = self.equity_high
        self.daily_profit_loss = 0
        self.session_start = 0
        self.last_logged_deal_ticket = 0
        self.active_orders = []
        self.base_magic = BASE_MAGIC
        self.last_trading_day = None
        self.cached_data = {
            'account_info': None,
            'positions': [],
            'orders': []
        }
        
        # Initialize symbol contexts
        self.symbol_contexts = {}
        for symbol in SYMBOLS:
            self.symbol_contexts[symbol] = {
                'last_trade_bar': {tf: -10 for tf in TIMEFRAMES},
                'atr_current': {tf: 0 for tf in TIMEFRAMES},
                'last_trade_time': {tf: 0 for tf in TIMEFRAMES},
                'last_processed_bar': {tf: 0 for tf in TIMEFRAMES},
                'last_order_placement': {tf: 0 for tf in TIMEFRAMES}
            }
        
        # Preload symbol data to ensure availability
        self.preload_symbol_data()
        
        if ENABLE_TRADE_JOURNAL:
            self.initialize_trade_journal()
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
    
    def initialize_mt5(self):
        """Initialize MT5 connection with credentials"""
        try:
            # Shutdown any existing connection
            try:
                mt5.shutdown()
                time.sleep(2)
            except:
                pass  # Ignore errors if not connected
            
            # Initialize with new credentials
            self.logger.info(f"Connecting to {MT5_SERVER} as account {MT5_ACCOUNT}")
            if not mt5.initialize(login=MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER):
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            # Verify connection
            if not mt5.terminal_info().connected:
                self.logger.error("MT5 not connected to server")
                return False
                
            self.logger.info(f"Connected to {MT5_SERVER} as account {MT5_ACCOUNT}")
            
            # Ensure all symbols are visible
            for symbol in SYMBOLS:
                if not mt5.symbol_select(symbol, True):
                    self.logger.warning(f"Could not select {symbol} in Market Watch")
            
            return True
        except Exception as e:
            self.logger.exception(f"MT5 initialization error: {e}")
            return False
    
    def preload_symbol_data(self):
        """Preload data for all symbols to ensure availability"""
        self.logger.info("Preloading symbol data...")
        for symbol in SYMBOLS:
            # Ensure symbol is selected in Market Watch
            if not mt5.symbol_select(symbol, True):
                self.logger.warning(f"Failed to select {symbol} in Market Watch")
                continue
                
            for timeframe in TIMEFRAMES:
                try:
                    # Load 1 bar to initialize symbol data
                    bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
                    if bars is None or len(bars) == 0:
                        self.logger.warning(f"No initial data for {symbol} TF:{timeframe}")
                    else:
                        self.logger.info(f"Preloaded data for {symbol} TF:{timeframe}")
                except Exception as e:
                    self.logger.error(f"Preload error for {symbol} TF:{timeframe}: {e}")
    
    def check_connection(self):
        """Ensure we're still connected to MT5 with retry logic"""
        try:
            # Reinitialize if not connected
            if not mt5.terminal_info().connected:
                self.logger.warning("MT5 connection lost. Reconnecting...")
                return self.initialize_mt5()
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return self.initialize_mt5()
    
    def calculate_drawdown(self, current_equity):
        """Safely calculate drawdown percentage"""
        if self.equity_high == 0:  # Prevent division by zero
            return 0
        return (self.equity_high - current_equity) / self.equity_high * 100
    
    def initialize_trade_journal(self):
        try:
            with open(JOURNAL_FILENAME, 'a') as f:
                if f.tell() == 0:  # File is empty
                    header = "Time,Symbol,Type,Volume,Price,Profit,Comment,Magic,SL,TP"
                    f.write(header + "\n")
        except Exception as e:
            self.logger.error(f"Journal init error: {e}")
    
    def log_trade(self, position):
        if not ENABLE_TRADE_JOURNAL:
            return
        
        try:
            magic = position.magic
            # Only log trades with magic numbers in our range
            if magic < self.base_magic or magic >= self.base_magic + 12000:
                return
                
            data = {
                'Time': pd.to_datetime(position.time, unit='s').strftime('%Y-%m-%d %H:%M:%S'),
                'Symbol': position.symbol,
                'Type': "BUY" if position.type == mt5.ORDER_TYPE_BUY else "SELL",
                'Volume': position.volume,
                'Price': position.price_open,
                'Profit': position.profit,
                'Comment': position.comment,
                'Magic': position.magic,
                'SL': position.sl,
                'TP': position.tp
            }
            
            with open(JOURNAL_FILENAME, 'a') as f:
                f.write(','.join(str(x) for x in data.values()) + '\n')
                
        except Exception as e:
            self.logger.error(f"Trade logging failed: {e}")
    
    def run(self):
        self.logger.info("Starting trading engine...")
        last_check_time = 0
        self.running = True  # Set running flag
        
        while self.running:
            current_time = time.time()
            
            # Process every 5 seconds
            if current_time - last_check_time >= 5:
                last_check_time = current_time
                self.on_timer()
                
            time.sleep(0.1)  # Reduce CPU usage
    
    def graceful_shutdown(self, signum, frame):
        self.logger.info("Shutting down gracefully...")
        self.running = False
        mt5.shutdown()
        self.logger.info("Shutdown complete")
    
    def refresh_cached_data(self):
        """Cache frequently accessed data to reduce MT5 calls"""
        try:
            self.cached_data['account_info'] = mt5.account_info()
            self.cached_data['positions'] = mt5.positions_get()
            self.cached_data['orders'] = mt5.orders_get()
        except Exception as e:
            self.logger.error(f"Data refresh error: {e}")
    
    def on_timer(self):
        # Check connection before anything else
        if not self.check_connection():
            self.logger.warning("Could not connect to MT5. Skipping cycle.")
            return
            
        # Refresh cached data
        self.refresh_cached_data()
        
        account_info = self.cached_data['account_info']
        if not account_info:
            self.logger.warning("No account info available")
            return
            
        current_equity = account_info.equity
        
        # Update equity high watermark
        if current_equity > self.equity_high:
            self.equity_high = current_equity
        
        # Reset daily P&L at session start
        if self.is_new_trading_day():
            self.equity_at_start = current_equity
            self.daily_profit_loss = 0
        
        # Calculate daily loss limit (percentage-based)
        daily_loss_limit = self.equity_at_start * (DAILY_LOSS_PERCENT / 100)
        
        # Prop firm risk checks
        if self.daily_profit_loss <= -daily_loss_limit:
            self.logger.warning(f"Daily loss limit reached: {self.daily_profit_loss}")
            return
            
        # Safe drawdown calculation
        drawdown = self.calculate_drawdown(current_equity)
        if drawdown >= MAX_DRAWDOWN_PERCENT:
            self.logger.warning(f"Max drawdown reached: {drawdown}%")
            return
        
        # Clean up expired orders
        self.cleanup_orders()
        
        # Skip processing if session not active
        if ENABLE_SESSION and not self.is_trading_session():
            return
        
        # Process each symbol/timeframe
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                self.process_symbol_timeframe(symbol, timeframe)
    
    def is_new_trading_day(self):
        """Check if it's a new trading day (00:00 Lagos time)"""
        try:
            now = datetime.datetime.now(pytz.utc)
            lagos_time = now.astimezone(pytz.timezone('Africa/Lagos'))
            current_date = lagos_time.date()
            
            if self.last_trading_day != current_date:
                # Check if it's a valid trading day (Sunday-Friday)
                if lagos_time.weekday() in [6, 0, 1, 2, 3, 4]:  # Sun-Fri
                    self.last_trading_day = current_date
                    self.logger.info(f"New trading day: {current_date}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Trading day check error: {e}")
            return False
    
    def is_trading_session(self):
        if not ENABLE_SESSION:
            return True
            
        try:
            now = datetime.datetime.now(pytz.utc)
            lagos_time = now.astimezone(pytz.timezone('Africa/Lagos'))
            
            # Sunday session starts at 22:15 Lagos time
            if lagos_time.weekday() == 6:  # Sunday
                if lagos_time.hour < SUNDAY_OPEN_HOUR or (
                    lagos_time.hour == SUNDAY_OPEN_HOUR and lagos_time.minute < SUNDAY_OPEN_MIN):
                    return False
                return True
            
            # Friday session ends at 21:45 Lagos time
            if lagos_time.weekday() == 4:  # Friday
                if lagos_time.hour > DAILY_CLOSE_HOUR or (
                    lagos_time.hour == DAILY_CLOSE_HOUR and lagos_time.minute >= DAILY_CLOSE_MIN):
                    return False
                return True
            
            # Saturday - no trading
            if lagos_time.weekday() == 5:
                return False
            
            # Monday-Thursday: full session
            return True
        except Exception as e:
            self.logger.error(f"Session check error: {e}")
            return False
    
    def get_timeframe_seconds(self, timeframe):
        """Convert timeframe to seconds"""
        return {
            1: 60,         # M1
            5: 300,        # M5
            15: 900,       # M15
            30: 1800,      # M30
            60: 3600,      # H1
            240: 14400,    # H4
            1440: 86400,   # D1
        }.get(timeframe, 300)  # Default to 5 minutes
    
    def cleanup_orders(self):
        current_orders = self.cached_data['orders']
        
        # Remove expired orders from active list
        for order in self.active_orders[:]:
            # Check if order still exists
            if not any(o.ticket == order.ticket for o in current_orders):
                self.active_orders.remove(order)
                continue
                
            # Check expiration by bars
            try:
                current_bars = mt5.copy_rates_from_pos(order.symbol, order.timeframe, 0, 1)
                if current_bars is None or len(current_bars) == 0:
                    continue
                    
                if current_bars[0][0] - order.placement_bar >= ORDER_EXPIRATION_BARS:
                    mt5.order_send({
                        'action': mt5.TRADE_ACTION_REMOVE, 
                        'order': order.ticket
                    })
                    self.active_orders.remove(order)
                    self.logger.info(f"Removed expired order #{order.ticket}")
            except Exception as e:
                self.logger.error(f"Order cleanup error: {e}")
    
    def get_bars_count(self, symbol, timeframe):
        try:
            bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
            return bars[0][0] if bars is not None and len(bars) > 0 else 0
        except Exception as e:
            self.logger.error(f"Bars count error for {symbol} TF:{timeframe}: {e}")
            return 0
    
    def count_orders(self, symbol, magic):
        count = 0
        
        # Count positions
        positions = self.cached_data['positions']
        if positions:
            count += sum(1 for p in positions if p.symbol == symbol and p.magic == magic)
        
        # Count active orders
        orders = self.cached_data['orders']
        if orders:
            count += sum(1 for o in orders if o.symbol == symbol and o.magic == magic)
        
        return count
    
    def manage_existing_positions(self, symbol, timeframe, trailing_factor):
        positions = self.cached_data['positions']
        if not positions:
            return
            
        for position in positions:
            if position.symbol != symbol:
                continue
                
            # Calculate magic number for this symbol/timeframe
            symbol_idx = SYMBOLS.index(symbol)
            timeframe_idx = TIMEFRAMES.index(timeframe)
            magic = self.base_magic + symbol_idx * 1000 + timeframe_idx * 10
            
            if position.magic != magic:
                continue
                
            try:
                symbol_info = mt5.symbol_info(symbol)
                if not symbol_info:
                    continue
                    
                point = symbol_info.point
                current_price = symbol_info.ask if position.type == mt5.ORDER_TYPE_BUY else symbol_info.bid
                profit = position.profit
                entry_price = position.price_open
                current_sl = position.sl
                current_tp = position.tp
                volume = position.volume
                new_sl = current_sl
                new_tp = current_tp
                
                # Calculate dollar risk per point
                dollar_per_point = RiskManager.calculate_dollar_risk_per_point(symbol)
                if dollar_per_point <= 0:
                    continue
                    
                # Calculate value per point for this position
                point_value = volume * dollar_per_point
                if point_value <= 0:
                    continue
                
                # Calculate profit units in $amount increments
                profit_units = int(profit / RISK_PER_TRADE)
                
                # Only trail when we have at least one unit of profit
                if profit_units < 1:
                    continue
                
                if profit_units >= 1:
                    if position.type == mt5.ORDER_TYPE_BUY:
                        # Calculate new SL based on profit units
                        new_sl = entry_price + profit_units * (RISK_PER_TRADE / point_value) * point
                        
                        # Additional ATR-based trailing for commodities
                        if symbol in ["XAUUSD", "USOIL", "XAGUSD"]:
                            atr_value = self.symbol_contexts[symbol]['atr_current'].get(timeframe, 0)
                            if atr_value > 0:
                                atr_sl = current_price - trailing_factor * atr_value
                                new_sl = max(new_sl, atr_sl)
                        
                        # Adjust TP to maintain risk/reward ratio
                        sl_distance = entry_price - new_sl
                        new_tp = entry_price + (sl_distance * RISK_REWARD_RATIO)
                        
                        # Handle initial SL (None or 0) and ensure new SL is valid
                        if (new_sl > (current_sl or 0) and new_sl < current_price):
                            self.modify_position(position.ticket, new_sl, new_tp)
                    
                    else:  # SELL position
                        new_sl = entry_price - profit_units * (RISK_PER_TRADE / point_value) * point
                        
                        if symbol in ["XAUUSD", "USOIL", "XAGUSD"]:
                            atr_value = self.symbol_contexts[symbol]['atr_current'].get(timeframe, 0)
                            if atr_value > 0:
                                atr_sl = current_price + trailing_factor * atr_value
                                new_sl = min(new_sl, atr_sl)
                        
                        sl_distance = new_sl - entry_price
                        new_tp = entry_price - (sl_distance * RISK_REWARD_RATIO)
                        
                        # Handle initial SL (None or 0) and ensure new SL is valid
                        if (new_sl < (current_sl or float('inf')) and 
                            new_sl > current_price):
                            self.modify_position(position.ticket, new_sl, new_tp)
            except Exception as e:
                self.logger.error(f"Position management error: {e}")
    
    def modify_position(self, ticket, sl, tp):
        try:
            request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': ticket,
                'sl': sl,
                'tp': tp
            }
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.warning(f"Position modify failed: {result.comment} (Error: {result.retcode})")
            else:
                self.logger.info(f"Modified position #{ticket} SL={sl} TP={tp}")
        except Exception as e:
            self.logger.error(f"Position modify error: {e}")
    
    def process_symbol_timeframe(self, symbol, timeframe):
        # Skip if at max global trades
        positions = self.cached_data['positions']
        orders = self.cached_data['orders']
        if len(positions) + len(orders) >= MAX_GLOBAL_TRADES:
            return
        
        # Bar check for minimum trade spacing
        current_bars = self.get_bars_count(symbol, timeframe)
        last_trade_bar = self.symbol_contexts[symbol]['last_trade_bar'][timeframe]
        if current_bars - last_trade_bar < MIN_BARS_BETWEEN_TRADES:
            return
        
        # Get symbol-specific settings
        settings = SYMBOL_SETTINGS.get(symbol, {})
        min_ma_gap = settings.get('minMaGap', MIN_MA_GAP)
        sl_factor = settings.get('slFactor', STOP_LOSS_ATR_FACTOR)
        trailing_factor = settings.get('trailingFactor', TRAILING_STOP_ATR_FACTOR)
        rsi_upper = settings.get('rsiUpper', 70)
        rsi_lower = settings.get('rsiLower', 30)
        atr1_period = settings.get('atr1Period', ATR1_PERIOD)
        atr2_period = settings.get('atr2Period', ATR2_PERIOD)
        
        # Get indicator values
        indicators = Indicators.get_indicators(symbol, timeframe, MA1_PERIOD, MA2_PERIOD, 
                                              atr1_period, atr2_period, RSI_PERIOD)
        if not indicators:
            return
            
        # Update context
        self.symbol_contexts[symbol]['atr_current'][timeframe] = indicators['atr_fast'][-1]
        
        # Spread check
        spread = Indicators.get_spread(symbol)
        avg_spread = Indicators.get_avg_spread(symbol)
        if spread > avg_spread * MAX_SPREAD_MULTIPLIER:
            self.logger.warning(f"High spread on {symbol}: {spread} > {avg_spread * MAX_SPREAD_MULTIPLIER}")
            return
        
        # Trade conditions
        gap = indicators['ma_fast'][-1] * min_ma_gap / 100
        close = indicators['close']  # Current close price
        
        buy_condition = (ENABLE_BUY and 
                        indicators['atr_fast'][-1] < indicators['atr_slow'][-1] and
                        close < indicators['ma_fast'][-1] - gap and
                        close > indicators['ma_slow'][-1] and
                        indicators['rsi'][-2] > indicators['rsi'][-1] and 
                        indicators['rsi'][-1] < rsi_upper)
        
        sell_condition = (ENABLE_SELL and 
                         indicators['atr_fast'][-1] < indicators['atr_slow'][-1] and
                         close > indicators['ma_fast'][-1] + gap and
                         close < indicators['ma_slow'][-1] and
                         indicators['rsi'][-2] < indicators['rsi'][-1] and 
                         indicators['rsi'][-1] > rsi_lower)
        
        # Position management
        self.manage_existing_positions(symbol, timeframe, trailing_factor)
        
        # Calculate unique magic number
        symbol_idx = SYMBOLS.index(symbol)
        timeframe_idx = TIMEFRAMES.index(timeframe)
        magic = self.base_magic + symbol_idx * 1000 + timeframe_idx * 10
        
        # Count existing orders and positions
        existing_orders = self.count_orders(symbol, magic)
        
        # New trade logic
        if (buy_condition or sell_condition) and existing_orders < MAX_TRADES_PER_SYMBOL_TF:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return
                
            pip_size = symbol_info.point * 10
            ask = symbol_info.ask
            bid = symbol_info.bid
            atr_value = indicators['atr_fast'][-1]
            
            if buy_condition:
                try:
                    buy_limit_price = ask - LIMIT_ORDER_DISTANCE * pip_size
                    buy_sl = buy_limit_price - sl_factor * atr_value
                    buy_tp = buy_limit_price + (sl_factor * atr_value * RISK_REWARD_RATIO)
                    
                    # Calculate initial lot size
                    initial_lots = RiskManager.calculate_lot_size(symbol, buy_limit_price, buy_sl, RISK_PER_TRADE)
                    
                    # Check if we need to adjust for max lot size
                    if initial_lots >= MAX_ALLOWED_LOT_SIZE:
                        # Adjust SL/TP to maintain $50 risk with max lot size
                        buy_sl, buy_tp = RiskManager.adjust_risk_for_fixed_dollar(
                            symbol, buy_sl, buy_tp, buy_limit_price, MAX_ALLOWED_LOT_SIZE, True, atr_value)
                        lots = MAX_ALLOWED_LOT_SIZE
                    else:
                        lots = initial_lots
                    
                    # Final validation
                    if lots < MIN_LOT_SIZE:
                        self.logger.warning(f"Lot size too small for {symbol}: {lots}")
                        return
                        
                    # Place order
                    if lots > 0:
                        order_ticket = self.place_order(
                            symbol, mt5.ORDER_TYPE_BUY_LIMIT, lots, buy_limit_price, buy_sl, buy_tp, magic, timeframe)
                        if order_ticket:
                            self.symbol_contexts[symbol]['last_trade_bar'][timeframe] = current_bars
                            self.symbol_contexts[symbol]['last_trade_time'][timeframe] = time.time()
                            self.active_orders.append(PendingOrder(
                                order_ticket, symbol, timeframe, time.time(), current_bars, magic))
                            self.logger.info(f"BUY LIMIT placed on {symbol} TF:{timeframe} Lots:{lots} Magic:{magic}")
                except Exception as e:
                    self.logger.error(f"Buy order error for {symbol}: {e}")
            
            elif sell_condition:
                try:
                    sell_limit_price = bid + LIMIT_ORDER_DISTANCE * pip_size
                    sell_sl = sell_limit_price + sl_factor * atr_value
                    sell_tp = sell_limit_price - (sl_factor * atr_value * RISK_REWARD_RATIO)
                    
                    # Calculate initial lot size
                    initial_lots = RiskManager.calculate_lot_size(symbol, sell_limit_price, sell_sl, RISK_PER_TRADE)
                    
                    # Check if we need to adjust for max lot size
                    if initial_lots >= MAX_ALLOWED_LOT_SIZE:
                        # Adjust SL/TP to maintain $50 risk with max lot size
                        sell_sl, sell_tp = RiskManager.adjust_risk_for_fixed_dollar(
                            symbol, sell_sl, sell_tp, sell_limit_price, MAX_ALLOWED_LOT_SIZE, False, atr_value)
                        lots = MAX_ALLOWED_LOT_SIZE
                    else:
                        lots = initial_lots
                    
                    # Final validation
                    if lots < MIN_LOT_SIZE:
                        self.logger.warning(f"Lot size too small for {symbol}: {lots}")
                        return
                        
                    # Place order
                    if lots > 0:
                        order_ticket = self.place_order(
                            symbol, mt5.ORDER_TYPE_SELL_LIMIT, lots, sell_limit_price, sell_sl, sell_tp, magic, timeframe)
                        if order_ticket:
                            self.symbol_contexts[symbol]['last_trade_bar'][timeframe] = current_bars
                            self.symbol_contexts[symbol]['last_trade_time'][timeframe] = time.time()
                            self.active_orders.append(PendingOrder(
                                order_ticket, symbol, timeframe, time.time(), current_bars, magic))
                            self.logger.info(f"SELL LIMIT placed on {symbol} TF:{timeframe} Lots:{lots} Magic:{magic}")
                except Exception as e:
                    self.logger.error(f"Sell order error for {symbol}: {e}")
    
    def place_order(self, symbol, order_type, volume, price, sl, tp, magic, timeframe):
        try:
            # Calculate expiration based on timeframe
            timeframe_seconds = self.get_timeframe_seconds(timeframe)
            expiration_seconds = ORDER_EXPIRATION_BARS * timeframe_seconds
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "magic": magic,
                "comment": "Xtley 001 Gap EA",
                "type_time": mt5.ORDER_TIME_SPECIFIED,
                "expiration": int(time.time()) + expiration_seconds
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # Add detailed error information
                error_msg = f"Order failed for {symbol}: {result.comment} (Error: {result.retcode})"
                self.logger.warning(error_msg)
                return None
                
            return result.order
        except Exception as e:
            self.logger.error(f"Order placement error: {e}")
            return None

if __name__ == "__main__":
    engine = TradingEngine()
    try:
        engine.run()
    except Exception as e:
        engine.logger.exception("Fatal error in main loop")
        mt5.shutdown()