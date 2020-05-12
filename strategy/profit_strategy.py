import copy
import pandas as pd
import numpy as np
from strategy.base_strategy import BaseStrategy
import talib
from utils.tools import round_to
import math
from collections import deque
from utils import fileutil


class ProfitStrategy(BaseStrategy):
    """
    网格策略
    """

    def __init__(self):
        self.profit_per = 0.1   # 利润要求
        self.d = "none"
        super(ProfitStrategy, self).__init__()

    def calculate_signal(self):
        trades = copy.copy(self.trades)
        last_trades = trades.get("market." + self.mark_symbol + ".trade.detail")
        if last_trades and len(last_trades) > 0:
            self.last_price = round_to(float(last_trades[-1].price), self.price_tick)
        if self.last_price <= 0:
            return
        position = copy.copy(self.position)
        klines = copy.copy(self.klines)
        df = klines.get("market." + self.mark_symbol + ".kline." + self.period)
        df['fast_ema'] = talib.EMA(df['close'], timeperiod=5)
        df['slow_ema'] = talib.EMA(df['close'], timeperiod=10)

        current_bar = df.iloc[-1]  # 最新的K线 Bar.
        last_bar = df.iloc[-2]
        self.d = "none"
        if current_bar["fast_ema"] > current_bar["slow_ema"] and last_bar["fast_ema"] <= last_bar["slow_ema"]:
            self.d = "long"
        if current_bar["fast_ema"] < current_bar["slow_ema"] and last_bar["fast_ema"] >= last_bar["slow_ema"]:
            self.d = "short"
        if self.d == "long":  # 开多仓
            if position.long_quantity > 0 and position.long_avg_price > 0:
                temp_profit = (last_trades - position.long_avg_price) * self.lever_rate/position.long_avg_price
                if temp_profit > self.profit_per:
                    self.long_status = -1
            elif position.long_quantity == 0 and position.long_avg_price == 0:
                self.long_status = 1
                self.long_trade_size = self.min_volume

        if self.d == "short":  # 开空仓
            if position.short_quantity > 0 and position.short_avg_price > 0:
                temp_profit = (position.short_avg_price - last_trades) * self.lever_rate/position.short_avg_price
                if temp_profit > self.profit_per:
                    self.short_status = -1
            elif position.short_quantity == 0 and position.short_avg_price == 0:
                self.short_status = 1
                self.short_trade_size = self.min_volume




