from api.huobi.sub.base_sub import BaseSub
from utils import logger
from utils import tools


class PositonSub(BaseSub):
    """
    持仓订阅
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
        if self._platform == "swap":
            self._ch = "positions.{symbol}".format(symbol=self._contract_type)
        else:
            self._ch = "positions.{symbol}".format(symbol=self._symbol)

    def ch(self):
        return self._ch

    def symbol(self):
        return self._symbol

    def sub_data(self):
        data = {
            "op": "sub",
            "cid": tools.get_uuid1(),
            "topic": self._ch
        }
        return data

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
        logger.info("update position:", self._position.__str__(), caller=self)

