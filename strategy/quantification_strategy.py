import copy
from utils import tools
from utils import logger
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy
import talib
from api.model.error import Error
from api.model.tasks import SingleTask
from utils.tools import round_to
import math
from collections import deque


class QuantificationStrategy(BaseStrategy):
    """
    网格策略
    """

    def __init__(self):
        self.price_margin = []  # 设置网格价格
        self.position_weight = []  # 设置网格的仓位
        self.band = None  # 网格价格
        self.atr = 0  # 真实波幅
        self.atr_per = 0.05   # 最小网格高度要求
        self.min_index = -1  # 网格基准先位置
        self.grids = deque(maxlen=10)  # 记录价格在网格中的位置
        self.close_position_rate = 5  # 平仓价格倍数
        super(QuantificationStrategy, self).__init__()

    def reset_bank(self, df):
        reset = True
        # if self.band is None:
        #     reset = True
        # else:
        #     open_orders = copy.copy(self.orders)
        #     position = copy.copy(self.position)
        #     if len(open_orders) == 0 and position.short_quantity == 0 and position.long_quantity == 0:
        #         reset = True
        if reset:
            df["atr"] = talib.ATR(df["high"], df["low"], df["close"], 20)
            df["max_high"] = talib.MAX(df["high"], self.klines_max_size)
            df["min_low"] = talib.MIN(df["low"], self.klines_max_size)
            current_bar = df.iloc[-1]
            atr = current_bar["atr"]
            if current_bar["close"] * self.atr_per / self.lever_rate > atr:  # 网格高度达不到最小要求
                return
            self.atr = atr
            num = math.floor((current_bar["max_high"] - current_bar["min_low"])/self.atr)
            if num % 2 == 0:
                num = num + 1
            self.min_index = math.floor(num/2)
            self.grids.clear()
            self.price_margin = []
            self.position_weight = []
            for i in range(0, num):
                self.price_margin.append(round_to((i - self.min_index) * self.atr, self.price_tick))
                self.position_weight.append(1)
            # df['olhc'] = df[["open", "close", "high", "low"]].mean(axis=1)
            self.band = np.mean(df['close']) + np.array(self.price_margin) * np.std(df['close'])
            print(self.price_margin)
            print(self.position_weight)
            print(self.band)
            # 计算各个网格的价格
            if self.trading_curb == "long":
                pass
            elif self.trading_curb == "short":
                pass
            else:
                pass

    def calculate_signal(self):
        self.long_status = 0
        self.short_status = 0
        self.short_trade_size = 0
        self.long_trade_size = 0
        klines = copy.copy(self.klines)
        df = klines.get("market." + self.mark_symbol + ".kline." + self.period)
        self.reset_bank(df)
        if self.atr == 0:
            return
        current_bar = df.iloc[-1]
        band_size = len(self.band)
        grid = -3
        for i in range(0, band_size):
            if i == 0:
                if current_bar["close"] <= self.band[i] - self.atr * self.close_position_rate:
                    grid = -2
                    break
                if (self.band[i] - self.atr * self.close_position_rate) < current_bar["close"] <= self.band[i]:
                    grid = i
                    break
            if i == band_size -1:
                if current_bar["close"] >= self.band[i] + self.atr * self.close_position_rate:
                    grid = -1
                    break
                if self.band[i] <= current_bar["close"] < (self.band[i] + self.atr * self.close_position_rate) :
                    grid = i
                    break
            if i < self.min_index:
                if (self.band[i] - self.atr * self.close_position_rate) < current_bar["close"] <= self.band[i]:
                    grid = i
                    break
            if i > self.min_index:
                if self.band[i] <= current_bar["close"] < (self.band[i] + self.atr * self.close_position_rate):
                    grid = i
                    break

        # grid = pd.cut([current_bar["close"]], self.band, labels=self.position_weight_label)[0]
        if len(self.grids) == 0:
            self.grids.append(grid)
        if self.grids[-1] != grid:
            self.grids.append(grid)
        # if len(self.grids) == 1:

        # if grid == pos:
        #     self.long_status = -1
        #     self.short_status = -1
        # if grid < pos - 1:
        #     self.long_status = 1
        #     self.short_status = -1
        #     self.long_trade_size = self.position_weight[grid]
        # if grid > pos + 1:
        #     self.long_status = -1
        #     self.short_status = 1
        #     self.short_trade_size = self.position_weight[grid]



