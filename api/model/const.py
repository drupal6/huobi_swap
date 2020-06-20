# -*- coding:utf-8 -*-
from enum import Enum


KILINE_PERIOD = ["1min", "5min", "15min", "30min"]
CURB_PERIOD = [7, 6, 5, 4]
TRADE = {
    "1min":  60000,
    "5min": 300000,
    "15min": 900000,
    "30min": 1800000,
    "60min": 3600000,
    "4hour": 14400000,
    "1day": 86400000
}


class TradingCurb(Enum):
    LONG = "long"  # 只开多仓和平多仓
    SHORT = "short"  # 只开空仓和平空仓
    NONE = "none"  # 没有限制
    LOCK = "lock"  # 不交易
    SELL = "sell"  # 只能平仓
    BUY = "buy"  # 只能加仓
    LIMITLONGBUY = "limitlongbuy"  # 不能开多仓
    LIMITSHORTBUY = "limitshortbuy"  # 不能开空仓

