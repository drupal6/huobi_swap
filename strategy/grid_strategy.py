import copy
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy
import talib
from utils.tools import round_to
import math
from collections import deque
from utils import fileutil
from utils import logger
from utils import trend_util


class GridStrategy(BaseStrategy):
    """
    网格策略
    """

    def __init__(self):
        self.file_path = "../file/GridStrategy_%s.json"
        self.price_margin = []  # 设置网格价格
        self.long_position_weight = []  # 设置多网格的仓位
        self.short_position_weight = []  # 设置空网格的仓位
        self.position_weight_label = []  # 设置网格仓位标签
        self.band = []  # 网格价格
        self.auto_atr = False  # 是否自动计算atr True是 False固定atr
        self.atr = 0  # 真实波幅
        self.atr_per = 0.05   # 最小网格高度要求
        self.min_index = -1  # 网格基准线位置
        self.grids = deque(maxlen=5)  # 记录价格在网格中的位置
        self.close_long_position_rate = 10  # 平多仓价格atr倍数
        self.close_short_position_rate = 10  # 平空仓价格atr倍数
        self.margin_num_limit = 4  # 最少网格数量要求
        super(GridStrategy, self).__init__()
        self.load_file()

    def load_file(self):
        file_data = fileutil.load_json(self.file_path % self.mark_symbol)
        if len(file_data) > 0:
            self.price_margin = file_data.get("price_margin")
            self.long_position_weight = file_data.get("long_position_weight")
            self.short_position_weight = file_data.get("short_position_weight")
            self.position_weight_label = file_data.get("position_weight_label")
            self.band = file_data.get("band")
            self.atr = file_data.get("atr")
            self.min_index = file_data.get("min_index")
            self.trading_curb = file_data.get("trading_curb")
            self.long_position_weight_rate = file_data.get("long_position_weight_rate")
            self.short_position_weight_rate = file_data.get("short_position_weight_rate")
            self.close_long_position_rate = file_data.get("close_long_position_rate", self.close_long_position_rate)
            self.close_short_position_rate = file_data.get("close_short_position_rate", self.close_short_position_rate)
            last_grid = file_data.get("last_grid")
            second_grid = file_data.get("second_grid")
            if second_grid:
                self.grids.append(second_grid)
            if last_grid:
                self.grids.append(last_grid)

    def save_file(self):
        file_data = {
            "price_margin": self.price_margin,
            "long_position_weight": self.long_position_weight,
            "short_position_weight": self.short_position_weight,
            "position_weight_label": self.position_weight_label,
            "band": self.band,
            "atr": self.atr,
            "min_index": self.min_index,
            "long_position_weight_rate": self.long_position_weight_rate,
            "short_position_weight_rate": self.short_position_weight_rate,
            "close_long_position_rate": self.close_long_position_rate,
            "close_short_position_rate": self.close_short_position_rate,
            "trading_curb": self.trading_curb
        }
        if len(self.grids) > 0:
            file_data["last_grid"] = int(self.grids[-1])
        if len(self.grids) > 1:
            file_data["second_grid"] = int(self.grids[-2])
        fileutil.save_json(self.file_path % self.mark_symbol, file_data)

    def reset_bank(self, df):
        reset = False
        if len(self.band) == 0:
            reset = True
        else:
            open_orders = copy.copy(self.orders)
            position = copy.copy(self.position)
            if len(open_orders) == 0 and position.short_quantity - self.short_fixed_position == 0 \
                    and position.long_quantity - self.long_fixed_position == 0:
                reset = True
        if reset:
            self.atr = 0
            df["max_high"] = talib.MAX(df["high"], self.klines_max_size)
            df["min_low"] = talib.MIN(df["low"], self.klines_max_size)
            df["atr"] = talib.ATR(df["high"], df["low"], df["close"], 20)
            current_bar = df.iloc[-1]
            high = current_bar["max_high"]
            low = current_bar["min_low"]
            if self.auto_atr:  # 自动计算atr
                atr = current_bar["atr"]
                if current_bar["close"] * self.atr_per / self.lever_rate > atr:  # 网格高度达不到最小要求
                    print("atr1:", (current_bar["close"] * self.atr_per / self.lever_rate), "atr:", atr)
                    return
            else:  # 设置固定的atr
                atr = current_bar["close"] * self.atr_per / self.lever_rate
            num = math.floor((high - low)/atr)
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
            self.price_margin.append(round_to((-(self.min_index + self.close_long_position_rate) * self.atr), self.price_tick))
            for i in range(0, num):
                self.price_margin.append(round_to((i - self.min_index) * self.atr, self.price_tick))
            self.price_margin.append(round_to(((self.min_index + self.close_short_position_rate) * self.atr), self.price_tick))
            # df['olhc'] = df[["open", "close", "high", "low"]].mean(axis=1)
            std = np.std(df['close'])
            if std < 1:
                std = 1.7
            band = np.mean(df['close']) + np.array(self.price_margin) * std  # 计算各个网格的价格
            self.band = band.tolist()
            for i in range(0, num):  # 做多的情况 计算网格仓位
                if i == 0:
                    self.long_position_weight.append((num - 1))
                if i == num - 1:
                    self.long_position_weight.append(0)
                else:
                    self.long_position_weight.append((num - i - 1))
                self.position_weight_label.append(i)
            for i in range(0, num):  # 做空的情况 计算网格仓位
                if i == 0:
                    self.short_position_weight.append(0)
                if i == num - 1:
                    self.short_position_weight.append((num - 1))
                else:
                    self.short_position_weight.append((i + 1))
            self.position_weight_label.append(num)
            self.save_file()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        # 自动设置trade_curb
        self.change_curb(klines, position)
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
            self.save_file()
        if grid == -1 or grid == len(self.band):  # 平仓
            self.long_status = -1  # 平多
            self.short_status = -1  # 平空
            logger.info("平仓 grid:", grid, caller=self)
        else:
            add_new_grid = False
            if self.grids[-1] != grid:
                logger.info("last grid:", self.grids[-1], "new grid", grid, caller=self)
                self.grids.append(grid)
                self.save_file()
                add_new_grid = True
            if len(self.grids) == 1:  # 补仓
                # 开多仓
                self.long_status = 1
                self.long_trade_size = self.long_position_weight[grid]
                # 开空仓
                self.short_status = 1
                self.short_trade_size = self.short_position_weight[grid]
                return

            if add_new_grid and self.grids[-2] < self.grids[-1]:  # 向上
                # 加空仓
                self.short_status = 1
                self.short_trade_size = self.short_position_weight[grid]
                # 平多仓
                if grid > 0:
                    grid = grid - 1
                if position.long_quantity - self.long_fixed_position > self.long_position_weight[grid] * self.long_position_weight_rate:
                    self.long_status = 1
                    self.long_trade_size = self.long_position_weight[grid]
                return

            if add_new_grid and self.grids[-2] > self.grids[-1]:  # 向下
                # 加多仓
                self.long_status = 1
                self.long_trade_size = self.long_position_weight[grid]
                # 平空仓
                if grid < len(self.band) - 2:
                    grid = grid + 1
                if position.short_quantity - self.short_fixed_position > self.short_position_weight[grid] * self.short_position_weight_rate:
                    self.short_status = 1
                    self.short_trade_size = self.short_position_weight[grid]

    def show(self):
        msg = super(GridStrategy, self).show()
        band_str = "".join(str(self.band))
        band_size = str(len(self.band))
        grid_str = str(self.grids[-1])
        curr_price = str(self.band[self.grids[-1]])
        atr = str(self.atr)
        last_price = str(self.last_price)
        auto_atr = str(self.auto_atr)
        return "%s\nband:%s\nsize:%s\ngrid:%s\nprice:%s\nlast_price:%s\natr:%s\nauto_atr=%s" % \
               (msg, band_str, band_size, grid_str, curr_price, last_price, atr, auto_atr)