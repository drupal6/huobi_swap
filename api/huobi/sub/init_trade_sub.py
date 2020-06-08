from api.huobi.sub.base_sub import BaseSub
from utils import logger
from utils.recordutil import record
from api.model.error import Error
from api.model.tasks import SingleTask

import pandas as pd
pd.set_option("expand_frame_repr", False)


class InitTradeSub(BaseSub):
    """
    交易历史数据
    """

    def __init__(self, symbol, request, trades_max_size=2000):
        """
        symbol:交割合约如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        symbol:永久合约如"BTC_USD"
        """
        self._symbol = symbol
        self._request = request
        self._trades_max_size = trades_max_size
        self._ch = "market.{s}.trade.detail".format(s=self._symbol.upper())
        SingleTask.run(self._init)

    async def _init(self):
        success, error = await self._request.get_trades(contract_type=self._symbol, size=self._trades_max_size)
        if error:
            e = Error("init trades error. channel:" + self._ch)
            logger.error(e, "error:", error, caller=self)
            return
        await self.call_back(self._symbol, success)

    def ch(self):
        return "init_trades"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, _symbol, data):
        for datas in data["data"]:
            for tick in datas["data"]:
                record.record_trade(symbol=_symbol, tick=tick, init=True)
        record.init = True


