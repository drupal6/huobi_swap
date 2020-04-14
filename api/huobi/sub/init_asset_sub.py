from api.huobi.sub.base_sub import BaseSub
from api.model.asset import Asset
from utils import tools


class InitAssetSub(BaseSub):
    """
    初始化资产
    """

    def __init__(self, symbol, asset):
        """
        symbol:btc、bch
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
            if total > 0:
                assets[symbol] = {
                    "total": "%.8f" % total,
                    "free": "%.8f" % free,
                    "locked": "%.8f" % locked
                }
        if assets == self._asset.assets:
            update = False
        else:
            update = True
        self._asset.update = update
        self._asset.assets = assets
        self._asset.timestamp = data["ts"]

