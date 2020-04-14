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