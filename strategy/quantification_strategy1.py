import copy
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy
import talib
from utils.tools import round_to
import math
from collections import deque
from utils import fileutil


class QuantificationStrategy1(BaseStrategy):
    """
    网格策略
    """

    def __init__(self):
        self.file_path = "../file/QuantificationStrategy_%s.json"
        self.price_margin = []  # 设置网格价格
        self.long_position_weight = []  # 设置多网格的仓位
        self.short_position_weight = []  # 设置空网格的仓位
        self.position_weight_label = []  # 设置网格仓位标签
        self.band = []  # 网格价格
        self.atr = 0  # 真实波幅
        self.atr_per = 0.1   # 网格利润要求
        self.min_index = -1  # 网格基准先位置
        self.grids = deque(maxlen=10)  # 记录价格在网格中的位置
        self.close_position_rate = 5  # 平仓价格倍数
        self.margin_num_limit = 4  # 最少网格要求
        super(QuantificationStrategy1, self).__init__()
        self._load_file()

    def _load_file(self):
        file_data = fileutil.load_json(self.file_path % self.mark_symbol)
        if len(file_data) > 0:
            self.price_margin = file_data.get("price_margin")
            self.long_position_weight = file_data.get("long_position_weight")
            self.short_position_weight = file_data.get("short_position_weight")
            self.position_weight_label = file_data.get("position_weight_label")
            self.band = file_data.get("band")
            self.atr = file_data.get("atr")
            self.min_index = file_data.get("min_index")
            last_grid = file_data.get("last_grid")
            if last_grid:
                self.grids.append(last_grid)

    def _save_file(self):
        file_data = {
            "price_margin": self.price_margin,
            "long_position_weight": self.long_position_weight,
            "short_position_weight": self.short_position_weight,
            "position_weight_label": self.position_weight_label,
            "band": self.band,
            "atr": self.atr,
            "min_index": self.min_index
        }
        if len(self.grids) > 0:
            file_data["last_grid"] = int(self.grids[-1])
        print(file_data)
        fileutil.save_json(self.file_path % self.mark_symbol, file_data)

    def reset_bank(self, df):
        reset = False
        if len(self.band) == 0:
            reset = True
        else:
            open_orders = copy.copy(self.orders)
            position = copy.copy(self.position)
            if len(open_orders) == 0 and position.short_quantity == 0 and position.long_quantity == 0:
                reset = True
        if reset:
            self.atr = 0
            df["max_high"] = talib.MAX(df["high"], self.klines_max_size)
            df["min_low"] = talib.MIN(df["low"], self.klines_max_size)
            current_bar = df.iloc[-1]
            atr = current_bar["close"] * self.atr_per/self.lever_rate
            num = math.floor((current_bar["max_high"] - current_bar["min_low"])/atr)
            # print(num)
            if num < self.margin_num_limit:  # 网格太少
                return
            self.atr = atr
            if num % 2 == 0:
                num = num + 1
            self.min_index = math.floor(num/2)
            self.grids.clear()
            self.price_margin = []
            self.long_position_weight = []
            self.short_position_weight = []
            self.position_weight_label = []
            self.price_margin.append(round_to((-(self.min_index + self.close_position_rate) * self.atr), self.price_tick))
            for i in range(0, num):
                self.price_margin.append(round_to((i - self.min_index) * self.atr, self.price_tick))
            self.price_margin.append(round_to(((self.min_index + self.close_position_rate) * self.atr), self.price_tick))
            # df['olhc'] = df[["open", "close", "high", "low"]].mean(axis=1)
            std = np.std(df['close'])
            if std < 1:
                std = 1.1
            if std > 3.5:
                std = 3.4
            band = np.mean(df['close']) + np.array(self.price_margin) * std  # 计算各个网格的价格
            self.band = band.tolist()
            for i in range(0, num):  # 做多的情况 计算网格仓位
                if i == 0:
                    self.long_position_weight.append((num - 1) * self.long_position_weight_rate)
                if i == num - 1:
                    self.long_position_weight.append(0)
                else:
                    self.long_position_weight.append((num - i - 1) * self.long_position_weight_rate)
                self.position_weight_label.append(i)
            for i in range(0, num):  # 做空的情况 计算网格仓位
                if i == 0:
                    self.short_position_weight.append(0)
                if i == num - 1:
                    self.short_position_weight.append((num - 1) * self.short_position_weight_rate)
                else:
                    self.short_position_weight.append((i + 1) * self.short_position_weight_rate)
            self.position_weight_label.append(num)
            self._save_file()
            print("std:", std, "atr:", self.atr, "min_index:", self.min_index, "num:", num)
            print("price_margin:", self.price_margin)
            print("band:", self.band)
            print("long_weight:", self.long_position_weight)
            print("short_weight:", self.short_position_weight)
            print("label:", self.position_weight_label)
            print("重置band")

    def calculate_signal(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        df = klines.get("market." + self.mark_symbol + ".kline." + self.period)
        self.reset_bank(df)
        if self.atr == 0:
            return
        current_bar = df.iloc[-1]
        if current_bar["close"] <= self.band[0]:
            grid = -1
        elif current_bar["close"] >= self.band[-1]:
            grid = len(self.band)
        else:
            grid = pd.cut([current_bar["close"]], self.band, labels=self.position_weight_label)[0]
        if len(self.grids) == 0:
            self.grids.append(grid)
            self._save_file()
        # print("grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
        #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
        #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
        if grid == -1 or grid == len(self.band):  # 平仓
            self.long_status = -1  # 平多
            self.short_status = -1  # 平空
            # print("平grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
            #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
            #       "short_weight:", self.short_position_weight,"close:", current_bar["close"])
        else:
            add_new_grid = False
            if self.grids[-1] != grid:
                self.grids.append(grid)
                self._save_file()
                add_new_grid = True
            if len(self.grids) == 1:  # 补仓
                if self.trading_curb != "short":  # 开多仓
                    self.long_status = 1
                    self.long_trade_size = self.long_position_weight[grid]
                    # print("补多grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                    #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                    #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
                if self.trading_curb != "long":  # 开空仓
                    self.short_status = 1
                    self.short_trade_size = self.short_position_weight[grid]
                    # print("补空grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                    #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                    #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
                return

            if add_new_grid and self.grids[-2] < self.grids[-1]:  # 向上
                if self.trading_curb != "short":  # 平多仓
                    if grid > 0:
                        grid = grid - 1
                    if position.long_quantity > self.long_position_weight[grid]:
                        self.long_status = 1
                        self.long_trade_size = self.long_position_weight[grid]
                        # print("平多grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                        #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                        #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
                if self.trading_curb != "long":  # 加空仓
                    self.short_status = 1
                    self.short_trade_size = self.short_position_weight[grid]
                    # print("加空grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                    #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                    #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
                return

            if add_new_grid and self.grids[-2] > self.grids[-1]:  # 向下
                if self.trading_curb != "short":  # 加多仓
                    self.long_status = 1
                    self.long_trade_size = self.long_position_weight[grid]
                    # print("加多grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                    #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                    #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])
                if self.trading_curb != "long":  # 平空仓
                    if grid < len(self.band - 2):
                        grid = grid + 1
                    if position.short_quantity > self.short_position_weight[grid]:
                        self.short_status = 1
                        self.short_trade_size = self.short_position_weight[grid]
                        # print("平空grids:", self.grids, "grid:", grid, "longPosition:", position.long_quantity,
                        #       "shortPosition:", position.short_quantity, "long_weight:", self.long_position_weight,
                        #       "short_weight:", self.short_position_weight, "close:", current_bar["close"])







