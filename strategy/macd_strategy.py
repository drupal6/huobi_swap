import talib
from strategy.base_strategy import BaseStrategy
import copy
import numpy as np
from utils import logger


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    """

    def __init__(self):
        super(MACDStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        df = klines.get("market."+self.mark_symbol+".kline." + self.period)
        df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12, slowperiod=16, signalperiod=9)

        current_bar = df.iloc[-1]  # 最新的K线 Bar.
        last_bar = df.iloc[-2]
        if current_bar["ma"] > current_bar["signal"] and last_bar["ma"] <= last_bar["signal"]:
            self.long_status == 1
            self.long_trade_size = self.min_volume
            self.short_status == -1
            logger.info("开多平空", self.last_price, caller=self)

        if current_bar["ma"] < current_bar["signal"] and last_bar["ma"] >= last_bar["signal"]:
            self.long_status == -1
            self.short_status == 1
            self.short_trade_size = self.min_volume
            logger.info("开空平多", self.last_price, caller=self)








