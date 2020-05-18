from api.huobi.sub.base_sub import BaseSub
from utils import logger


class InitPositonSub(BaseSub):
    """
    初始化持仓
    """

    def __init__(self, platform, symbol, contract_type, position):
        """
        symbol:交割合约btc、bch
        contract_type当周:"this_week", 次周:"next_week", 季度:"quarter"
        symbol:永续合约BTC
        contract_type续合约:"BTC-USD"
        """
        self._platform = platform
        self._symbol = symbol
        self._position = position
        self._contract_type = contract_type

    def ch(self):
        return "positions"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, topic, data):
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
            if position_info["direction"] == "buy":
                self._position.long_quantity = int(position_info["volume"])
                self._position.long_avg_price = position_info["cost_hold"]
                self._position.long_avg_open_price = position_info["cost_open"]
            else:
                self._position.short_quantity = int(position_info["volume"])
                self._position.short_avg_price = position_info["cost_hold"]
                self._position.short_avg_open_price = position_info["cost_open"]
            self._position.utime = int(data["ts"])
        self._position.init = True
        logger.info("init position:", self._position.__str__(), caller=self)

