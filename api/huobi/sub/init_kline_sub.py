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

    def __init__(self, strategy, period):
        """
        strategy:策略类
        symbol:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        symbol:如"BTC_USD"...
        period:1min, 5min, 15min, 30min, 60min,4hour,1day,1week, 1mon
        """
        self._strategy = strategy
        self._symbol = self._strategy.mark_symbol
        self._max_size = self._strategy.klines_max_size
        self._period = period
        self._ch = "market.{s}.kline.{p}".format(s=self._symbol.upper(), p=self._period)
        SingleTask.run(self._init)

    async def _init(self):
        success, error = await self._strategy.request.get_klines(contract_type=self._symbol, period=self._period,
                                                                 size=self._max_size)
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
        history_data = data.get("data")
        df = pd.DataFrame(history_data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                 'high': 6, 'amount': 7})
        df = df[['id', 'open', 'high', 'low', 'close', 'amount']]
        self._strategy.klines[channel] = df


