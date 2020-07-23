from api.huobi.sub.base_sub import BaseSub
from utils import logger


class InitPositonSub(BaseSub):
    """
    初始化持仓
    """

    def __init__(self, strategy):
        """
        symbol:交割合约btc、bch
        contract_type当周:"this_week", 次周:"next_week", 季度:"quarter"
        symbol:永续合约BTC
        contract_type续合约:"BTC-USD"
        """
        self._strategy = strategy
        self._platform = self._strategy.platform
        self._symbol = self._strategy.symbol
        self._contract_type = self._strategy.trade_symbol

    def ch(self):
        return "positions"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, topic, data):
        event = data["event"]
        for position_info in data["data"]:
            if position_info["symbol"] != self._symbol.upper():
                continue
            if self._platform == "swap":
                if position_info["contract_code"] != self._contract_type:
                    return
            else:
                pass
                # if position_info["contract_type"] != self._contract_type:
                #     return
            volume = int(position_info["volume"])
            if position_info["direction"] == "buy":
                self._strategy.position.long_quantity = max(volume - self._strategy.long_fixed_position, 0)
                self._strategy.position.long_avg_price = position_info["cost_hold"]
                self._strategy.position.long_avg_open_price = position_info["cost_open"]
            else:
                self._strategy.position.short_quantity = max(volume - self._strategy.short_fixed_position, 0)
                self._strategy.position.short_avg_price = position_info["cost_hold"]
                self._strategy.position.short_avg_open_price = position_info["cost_open"]
            self._strategy.position.utime = int(data["ts"])
        self._strategy.position.init = True
        if event == "init":
            logger.info("init position:", self._strategy.position.__str__(), caller=self)

