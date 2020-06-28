import talib
from strategy.base_strategy import BaseStrategy
import copy
import numpy as np
from api.model.const import KILINE_PERIOD
from api.model.const import TradingCurb
from utils import logger


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    """

    def __init__(self):
        self.long_profit_per = 1  # 多利润要求
        self.short_profit_per = 1  # 多利润要求
        self.long_stop_loss_per = -1  # 多止损
        self.short_stop_loss_per = -1  # 空止损
        super(MACDStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)

        self.change_curb(klines, position)

        if self.trading_curb == TradingCurb.LIMITSHORTBUY.value and position.long_quantity == 0:
            self.long_status = 1
            self.long_trade_size = self.min_volume
        if position.long_quantity > 0:
            temp_profit = (self.last_price - position.long_avg_open_price) * self.lever_rate / position.long_avg_open_price
            # 达到利润平多
            if temp_profit > self.long_profit_per:
                self.long_status = -1
                self.trading_curb = TradingCurb.SELL.value
            # 平多止损
            elif temp_profit <= self.long_stop_loss_per:
                self.long_status = -1
                self.trading_curb = TradingCurb.SELL.value

        if self.trading_curb == TradingCurb.LIMITLONGBUY.value and position.short_quantity == 0:
            self.short_status = 1
            self.short_trade_size = self.min_volume
        if position.short_quantity > 0:
            temp_profit = (position.short_avg_open_price - self.last_price) * self.lever_rate / position.short_avg_open_price
            # 达到利润平空
            if temp_profit > self.short_profit_per:
                self.short_status = -1
                self.trading_curb = TradingCurb.SELL.value
            # 平空止损
            elif temp_profit <= self.short_stop_loss_per:
                self.short_status = -1
                self.trading_curb = TradingCurb.SELL.value

    def change_curb(self, klines, position):
        if not self.auto_curb:
            return
        last_ma = 0
        last_signal = 0
        ma = 0
        signal = 0
        log_data = {}
        close = None
        for index, period in enumerate(KILINE_PERIOD):
            df = klines.get("market.%s.kline.%s" % (self.mark_symbol, period))
            df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12,
                                                            slowperiod=26, signalperiod=9)
            curr_bar = df.iloc[-1]
            ma = ma + curr_bar["ma"]
            signal = signal + curr_bar["signal"]
            log_data[period + "_ma"] = curr_bar["ma"]
            log_data[period + "_signal"] = curr_bar["signal"]
            if not close:
                close = curr_bar["close"]
            last_bar = df.iloc[-2]
            last_ma = last_ma + last_bar["ma"]
            last_signal = last_signal + last_bar["signal"]
        if position.long_quantity - self.long_fixed_position == 0 and \
                position.short_quantity - self.short_fixed_position == 0:
            if last_ma <= last_signal and ma > signal:
                self.trading_curb = TradingCurb.LIMITSHORTBUY.value
            elif last_ma >= last_signal and ma < signal:
                self.trading_curb = TradingCurb.LIMITLONGBUY.value
        log_data["ma"] = ma
        log_data["signal"] = signal
        log_data["trading_curb"] = self.trading_curb
        log_data["close"] = close
        logger.info("change_curb:", log_data)






