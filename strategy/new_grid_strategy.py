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


class NewGridStrategy(BaseStrategy):
    """
    新网格策略
    """

    def __init__(self):
        self.max_orders = 1
        self.atr_per = 0.05   # 最小网格高度要求
        self.same_order_limit = 1  # 同种类型订单数量限制
        super(NewGridStrategy, self).__init__()

    def strategy_handle(self):
        orders = copy.copy(self.orders)
        buy_long_orders = []
        buy_short_orders = []
        sell_long_orders = []
        sell_short_orders = []
        for order in orders.values():
            if order["status"] == 5 or order["status"] == 6 or order["status"] == 7:
                continue
            if order["offset"] == "open":
                if order["direction"] == "buy":
                    buy_long_orders.append(order)
                if order["direction"] == "sell":
                    buy_short_orders.append(order)
            if order["offset"] == "close":
                if order["direction"] == "buy":
                    sell_short_orders.append(order)
                if order["direction"] == "sell":
                    sell_long_orders.append(order)
        buy_long_size = len(buy_long_orders)
        buy_short_size = len(buy_short_orders)
        sell_long_size = len(sell_long_orders)
        sell_short_size = len(sell_short_orders)
        if buy_long_size == 0:
            # 开多单
            pass
        elif buy_long_size > self.same_order_limit:
            # 有多个开多单时要留下最小的
            pass

        if buy_short_size == 0:
            # 开空单
            pass
        elif buy_short_size > self.same_order_limit:
            # 有多个开空单时要留下最大的
            pass

        if sell_long_size == 0:
            # 平多单
            pass
        elif sell_long_size > self.same_order_limit:
            # 有多个平多单时要留下最小的
            pass

        if sell_short_size == 0:
            # 平空单
            pass
        elif sell_short_size > self.same_order_limit:
            # 有多个平空单时要留下最大的
            pass

