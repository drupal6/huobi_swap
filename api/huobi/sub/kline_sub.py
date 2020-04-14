from api.huobi.sub.base_sub import BaseSub
from api.model.kline import Kline
from utils import logger


class KlineSub(BaseSub):
    """
    k线订阅
    """

    def __init__(self, symbol, period, klines, klines_max_size=200):
        """
        symbol:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        period:1min, 5min, 15min, 30min, 60min,4hour,1day,1week, 1mon
        """
        self._symbol = symbol
        self._period = period
        self._klines = klines
        self._klines_max_size = klines_max_size
        self._ch = "market.{s}.kline.{p}".format(s=self._symbol.upper(), p=self._period)

    def ch(self):
        return self._ch

    def symbol(self):
        return self._symbol

    def period(self):
        return self._period

    def sub_data(self):
        data = {
            "sub": self._ch
        }
        return data

    async def call_back(self, channel, data):
        df = self._klines.get(channel)
        if df is None:
            logger.info("klines not init. channel:", self._ch)
            return
        d = data.get("tick")
        if int(df.iloc[-1]["id"]) == int(d["id"]):
            df.drop(df.index[-1], inplace=True)
        new_kline = [{'id': d["id"], 'open': d["open"], 'high': d["high"], 'low': d["low"], 'close': d["close"],
                      'amount': d["amount"]}]
        df = df.append(new_kline, ignore_index=True)
        if len(df) > self._klines_max_size:
            df.drop(df.index[0], inplace=True)
            df.reset_index(drop=True, inplace=True)
        self._klines[channel] = df



