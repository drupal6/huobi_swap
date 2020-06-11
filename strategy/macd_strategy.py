import talib
from strategy.base_strategy import BaseStrategy
import copy
import numpy as np
from utils import logger
from api.model.const import KILINE_PERIOD, CURB_PERIOD


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    """

    def __init__(self):
        self.long_profit_per = 0.3  # 多利润要求
        self.short_profit_per = 0.3  # 多利润要求
        self.long_stop_loss_per = -1  # 多止损
        self.short_stop_loss_per = -1  # 空止损
        super(MACDStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        curr_w = 0
        last_w = 0
        curr_price = None
        last_price = None
        max_weight = len(KILINE_PERIOD)
        select_index = KILINE_PERIOD.index(self.period)
        for index, period in enumerate(KILINE_PERIOD):
            df = klines.get("market." + self.mark_symbol + ".kline." + period)
            df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12,
                                                            slowperiod=26, signalperiod=9)
            curr_bar = df.iloc[-1]
            last_bar = df.iloc[-2]
            curr_d = curr_bar["ma"] - curr_bar["signal"]
            last_d = last_bar["ma"] - last_bar["signal"]
            if period == self.period:
                curr_price = curr_bar["close"]
                last_price = last_bar["close"]
            curr_w = curr_w + curr_d * (max_weight - abs(select_index - index))
            last_w = last_w + last_d * (max_weight - abs(select_index - index))

        if position.long_quantity == 0:
            if last_w < 0 and curr_w > 0:  # 开多
                self.long_status = 1
                self.long_trade_size = self.min_volume
        else:
            temp_profit = (self.last_price - position.long_avg_open_price) * self.lever_rate / position.long_avg_open_price
            # 达到利润平多
            if temp_profit > self.long_profit_per:
                self.long_status = -1
            # 平多止损
            elif temp_profit <= self.long_stop_loss_per:
                self.long_status = -1

        if position.short_quantity == 0:
            if last_w > 0 and curr_w < 0:  # 开空
                self.short_status = 1
                self.short_trade_size = self.min_volume
        else:
            temp_profit = (position.short_avg_open_price - self.last_price) * self.lever_rate / position.short_avg_open_price
            # 达到利润平空
            if temp_profit > self.short_profit_per:
                self.short_status = -1
            # 平空止损
            elif temp_profit <= self.short_stop_loss_per:
                self.short_status = -1









