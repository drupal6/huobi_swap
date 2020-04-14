# -*- coding:utf-8 -*-

"""
Market module.
"""

import json


class Orderbook:
    """ Orderbook object.

    Args:
        platform: Exchange platform name, e.g. huobi_swap.
        symbol: Trade pair name, e.g. BTC-USD.
        asks: Asks list, e.g. [[price, quantity], [...], ...]
        bids: Bids list, e.g. [[price, quantity], [...], ...]
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, asks=None, bids=None, timestamp=None):
        """ Initialize. """
        self.platform = platform
        self.symbol = symbol
        self.asks = asks
        self.bids = bids
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "asks": self.asks,
            "bids": self.bids,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Trade:
    """ Trade object.

    Args:
        platform: Exchange platform name, e.g. huobi_swap.
        symbol: Trade pair name, e.g. BTC-USD.
        action: Trade action, BUY or SELL.
        price: Order place price.
        quantity: Order place quantity.
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, action=None, price=None, quantity=None, timestamp=None):
        """ Initialize. """
        self.platform = platform
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Kline:
    """ Kline object.

    Args:
        platform: Exchange platform name, e.g. huobi_swap.
        id:周期初始时间
        symbol: Trade pair name, e.g. BTC-USD.
        open: Open price.
        high: Highest price.
        low: Lowest price.
        close: Close price.
        volume: 成交量张数
        amount: 成交量(币), 即 sum(每一笔成交量(张)*单张合约面值/该笔成交价)
        timestamp: 响应生成时间点，单位：毫秒
        kline_type: Kline type name, kline - 1min, kline_5min - 5min, kline_15min - 15min.
    """

    def __init__(self, id=None, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 amount=None, timestamp=None, kline_type=None):
        """ Initialize. """
        self.platform = platform
        self.id = id
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.amount = amount
        self.timestamp = timestamp
        self.kline_type = kline_type

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "id": self.id,
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "kline_type": self.kline_type
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)
