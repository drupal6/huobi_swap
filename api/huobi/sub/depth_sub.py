from api.huobi.sub.base_sub import BaseSub
from api.model.orderbook import Orderbook
from collections import deque


class DepthSub(BaseSub):
    """
    行情数据地订阅
    """

    def __init__(self, symbol, step, depths, depth_size=10, depths_max_size=200):
        """
        symbol:交割合约如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        symbol:永久合约如"BTC_USD"...
        step：获得150档深度数据，使用step0, step1, step2, step3, step4, step5（step1至step5是进行了深度合并后的深度），
        使用step0时，不合并深度获取150档数据;获得20档深度数据，使用 step6, step7, step8, step9, step10, step11（step7
        至step11是进行了深度合并后的深度），使用step6时，不合并深度获取20档数据
        """
        self._symbol = symbol
        self._step = step
        self._depths = depths
        self._depth_size = depth_size
        self._depths_max_size = depths_max_size
        self._ch = "market.{s}.depth.{d}".format(s=self._symbol.upper(), d=self._step)
        self._depths[self._ch] = deque(maxlen=self._depths_max_size)

    def ch(self):
        return self._ch

    def topic(self):
        return self._ch.lower()

    def symbol(self):
        return self._symbol

    def sub_data(self):
        data = {
            "sub": self._ch
        }
        return data

    async def call_back(self, channel, data):
        d = data.get("tick")
        asks, bids = [], []
        if d.get("asks"):
            for item in d.get("asks")[:self._depth_size]:
                price = "%.8f" % item[0]
                quantity = "%.8f" % item[1]
                asks.append([price, quantity])
        if d.get("bids"):
            for item in d.get("bids")[:self._depth_size]:
                price = "%.8f" % item[0]
                quantity = "%.8f" % item[1]
                bids.append([price, quantity])
        info = {
            "platform": "huobi",
            "symbol": self._step,
            "asks": asks,
            "bids": bids,
            "timestamp": d.get("ts")
        }
        orderbook = Orderbook(**info)
        depths = self._depths[channel]
        depths.append(orderbook)
