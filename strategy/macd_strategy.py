import talib
from strategy.base_strategy import BaseStrategy
import copy
import numpy as np
from utils import logger
from api.model.const import KILINE_PERIOD, CURB_PERIOD
from api.model.const import TradingCurb


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    """

    def __init__(self):
        self.long_profit_per = 0.5  # 多利润要求
        self.short_profit_per = 0.3  # 多利润要求
        self.long_stop_loss_per = -1  # 多止损
        self.short_stop_loss_per = -1  # 空止损
        super(MACDStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        self.change_curb(klines, position)

        if self.trading_curb == TradingCurb.LIMITLONGBUY.value and position.long_quantity == 0:
            self.long_status = 1
            self.long_trade_size = self.min_volume
        if position.long_quantity > 0:
            temp_profit = (self.last_price - position.long_avg_open_price) * self.lever_rate / position.long_avg_open_price
            # 达到利润平多
            if temp_profit > self.long_profit_per:
                self.long_status = -1
            # 平多止损
            elif temp_profit <= self.long_stop_loss_per:
                self.long_status = -1

        if self.trading_curb == TradingCurb.LIMITSHORTBUY.value and position.short_quantity == 0:
            self.short_status = 1
            self.short_trade_size = self.min_volume
        if position.short_quantity > 0:
            temp_profit = (position.short_avg_open_price - self.last_price) * self.lever_rate / position.short_avg_open_price
            # 达到利润平空
            if temp_profit > self.short_profit_per:
                self.short_status = -1
            # 平空止损
            elif temp_profit <= self.short_stop_loss_per:
                self.short_status = -1









