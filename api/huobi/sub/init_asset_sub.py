from api.huobi.sub.base_sub import BaseSub
from utils import logger


class InitAssetSub(BaseSub):
    """
    初始化资产
    """

    def __init__(self, symbol, asset):
        """
        交割合约symbol:btc、bch
        永久合约合约symbol:BTC-USD
        """
        self._symbol = symbol
        self._asset = asset

    def ch(self):
        return "accounts"

    def symbol(self):
        return self._symbol

    def sub_data(self):
        return None

    async def call_back(self, op, data):
        assets = {}
        for item in data["data"]:
            symbol = item["symbol"].upper()
            total = float(item["margin_balance"])
            free = float(item["margin_available"])
            locked = float(item["margin_frozen"])
            risk = item["risk_rate"]
            rate = item["lever_rate"]
            factor = item["adjust_factor"]
            liquidation = item["liquidation_price"]
            if total > 0:
                assets[symbol] = {
                    "total": "%.8f" % total,
                    "free": "%.8f" % free,
                    "locked": "%.8f" % locked,
                    "risk": risk,
                    "rate": rate,
                    "liquidation": liquidation,
                    "factor": factor
                }
        if assets == self._asset.assets:
            update = False
        else:
            update = True
        self._asset.update = update
        self._asset.assets = assets
        self._asset.timestamp = data["ts"]
        logger.info("init assets:", self._asset.__str__(), caller=self)

