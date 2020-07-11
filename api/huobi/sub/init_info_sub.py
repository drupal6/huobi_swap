from api.huobi.sub.base_sub import BaseSub
from utils import logger
from api.model.error import Error
from api.model.tasks import SingleTask
import pandas as pd
pd.set_option("expand_frame_repr", False)


class InitInfoSub(BaseSub):
    """
    初始合约信息
    """

    def __init__(self, strategy):
        self._strategy = strategy
        self._symbol = self._strategy.symbol
        self._platform = self._strategy.platform
        SingleTask.run(self._init)

    async def _init(self):
        if self._platform == "swap":
            success, error = await self._strategy.request.get_info(contract_code=self._strategy.trade_symbol)
        else:
            success, error = await self._strategy.request.get_info(symbol=self._strategy.symbol.upper(),
                                                                   contract_type=self._strategy.trade_symbol)
        if error:
            e = Error("init info error.")
            logger.error(e, "error:", error, caller=self)
            return
        await self.call_back("", success)

    def ch(self):
        return "init_ifo"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, channel, data):
        if data.get("status") == "ok":
            info_data = data.get("data")
            for info in info_data:
                if info["symbol"] == self._symbol:
                    self._strategy.contract_size = info.get("contract_size")
                    self._strategy.price_tick = info.get("price_tick")
        else:
            logger.error("init info error. error:", data, caller=self)


