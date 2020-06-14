import talib
from strategy.base_strategy import BaseStrategy
import copy
import numpy as np


class EmaStrategy(BaseStrategy):
    """
    macd
    """

    def __init__(self):
        self.long_rate = 0
        self.short_rate = 0
        super(EmaStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        lr = position.long_quantity / self.long_position_weight_rate
        sr = position.short_quantity / self.short_position_weight_rate
        if lr > self.long_rate:
            self.long_rate = lr
        if sr > self.short_rate:
            self.short_rate = sr
        print(">>>>", self.short_rate, self.long_rate)
        df = klines.get("market."+self.mark_symbol+".kline." + self.period)
        df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12,
                                                        slowperiod=26, signalperiod=9)

        current_bar = df.iloc[-1]  # 最新的K线 Bar.
        last_bar = df.iloc[-2]
        if current_bar["ma"] < 0 and last_bar["signal"] < 0:
            if current_bar["ma"] > current_bar["signal"] and last_bar["ma"] <= last_bar["signal"]:
                self.long_status = 1
                self.long_rate = self.long_rate + 1
                self.min_volume = self.min_volume * self.long_rate
                self.long_trade_size = self.min_volume
                self.short_status = -1
                self.short_rate = 0
        if current_bar["ma"] > 0 and last_bar["signal"] > 0:
            if current_bar["ma"] < current_bar["signal"] and last_bar["ma"] >= last_bar["signal"]:
                self.long_status = -1
                self.long_rate = 0
                self.short_status = 1
                self.short_rate = self.short_rate + 1
                self.min_volume = self.min_volume * self.short_rate
                self.short_trade_size = self.min_volume








