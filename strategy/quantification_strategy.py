import copy
from utils import tools
from utils import logger
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy


class QuantificationStrategy(BaseStrategy):
    """
    量化策略
    """

    def __init__(self):
        # 设置网格的仓位
        self.position_weight = [5, 4, 3, 2, 1, 1, 0, 1, 1, 2, 3, 4, 5]
        # 设置网格价格
        self.price_margin = [-10, -5, -3, -2, -1.4, -0.7, -0.3, 0.3, 0.7, 1.4, 2, 3 , 5, 10]
        # 网格区间
        self.position_weight_label = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.band = None
        self.band_set_time = 0
        self.band_set_period = 600000
        super(QuantificationStrategy, self).__init__()

    def calculate_signal(self):
        klines = copy.copy(self.klines)
        self.reset_bank(klines)
        df = klines.get("market."+self.mark_symbol+".kline." + self.period)
        current_bar = df.iloc[-1]
        grid = pd.cut([current_bar["close"]], self.band, labels=self.position_weight_label)[0]
        self.long_status = 0
        self.short_status = 0
        self.short_trade_size = 0
        self.long_trade_size = 0
        pos = int(len(self.position_weight) / 2)
        if grid == pos:
            self.long_status = -1
            self.short_status = -1
        if grid < pos - 1:
            self.long_status = 1
            self.short_status = -1
            self.long_trade_size = self.position_weight[grid]
        if grid > pos + 1:
            self.long_status = -1
            self.short_status = 1
            self.short_trade_size = self.position_weight[grid]

    def reset_bank(self, klines):
        reset = False
        if self.band is None:
            reset = True
        else:
            utime = tools.get_cur_timestamp_ms()
            if utime < self.band_set_period + self.band_set_time:
                return
            open_orders = copy.copy(self.orders)
            position = copy.copy(self.position)
            if len(open_orders) == 0 and position.short_quantity == 0 and position.long_quantity == 0:
                reset = True
        if reset:
            df = klines.get("market." + self.mark_symbol + ".kline." + self.period)
            # df['olhc'] = df[["open", "close", "high", "low"]].mean(axis=1)
            # 计算各个网格的价格
            self.band = np.mean(df['close']) + np.array(self.price_margin) * np.std(df['close'])
            logger.info("set band.", self.band, caller=self)
            self.band_set_time = tools.get_cur_timestamp_ms()
