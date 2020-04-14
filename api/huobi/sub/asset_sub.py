from api.huobi.sub.base_sub import BaseSub
from api.model.asset import Asset
from utils import tools


class AssetSub(BaseSub):
    """
    资产变动订阅
    """

    def __init__(self, symbol, asset):
        """
        symbol:btc、bch
        """
        self._symbol = symbol
        self._asset = asset
        self._ch = "accounts.{symbol}".format(symbol=self._symbol)

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


