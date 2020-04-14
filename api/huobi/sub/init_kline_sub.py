from api.huobi.sub.base_sub import BaseSub
from utils import logger
from collections import deque
from api.model.error import Error
from api.model.tasks import SingleTask
import pandas as pd
pd.set_option("expand_frame_repr", False)


class InitKlineSub(BaseSub):
    """
    k线订阅
    """

    def __init__(self, symbol, period, klines, request, klines_max_size=200):
        """
        symbol:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        period:1min, 5min, 15min, 30min, 60min,4hour,1day,1week, 1mon
        """
        self._symbol = symbol
        self._period = period
        self._klines = klines
        self._request = request
        self._klines_max_size = klines_max_size
        self._ch = "market.{s}.kline.{p}".format(s=self._symbol.upper(), p=self._period)
        SingleTask.run(self._init)

    async def _init(self):
        success, error = await self._request.get_klines(contract_type=self._symbol,
                                                        period=self._period,
                                                        size=self._klines_max_size)
        if error:
            e = Error("init kiline error. channel:" + self._ch)
            logger.error(e, "error:", error, caller=self)
            return
        await self.call_back(self._ch, success)

    def ch(self):
        return "init_klines"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, channel, data):
        history_klines = data.get("data")
        df = pd.DataFrame(history_klines, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                   'high': 6, 'amount': 7})
        df = df[['id', 'open', 'high', 'low', 'close', 'amount']]
        self._klines[channel] = df


