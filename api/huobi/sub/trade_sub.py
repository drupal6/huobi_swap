from api.huobi.sub.base_sub import BaseSub
from api.model.markettrade import Trade
from api.model.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from collections import deque
from utils.recordutil import record


class TradeSub(BaseSub):
    """
    交易订阅
    """

    def __init__(self, symbol, period, trades, trades_max_size=200):
        """
        symbol:交割合约如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        symbol:永久合约如"BTC_USD"
        """
        self._symbol = symbol
        self._period = period
        self._trades = trades
        self.trades_max_size = trades_max_size
        self._ch = "market.{s}.trade.detail".format(s=self._symbol.upper())
        self._trades[self._ch] = deque(maxlen=self.trades_max_size)

    def ch(self):
        return self._ch

    def symbol(self):
        return self._symbol

    def sub_data(self):
        data = {
            "sub": self._ch
        }
        return data

    async def call_back(self, channel, data):
        symbol = self._symbol
        platform = "huobi"
        ticks = data.get("tick")
        trades = list()
        for tick in ticks["data"]:
            direction = tick.get("direction")
            price = tick.get("price")
            quantity = tick.get("amount")
            info = {
                "platform": platform,
                "symbol": symbol,
                "action": ORDER_ACTION_BUY if direction == "buy" else ORDER_ACTION_SELL,
                "price": "%.8f" % price,
                "quantity": "%.8f" % quantity,
                "timestamp": tick.get("ts")
            }
            trade = Trade(**info)
            trades.append(trade)
            record.record_trade(symbol=symbol, tick=tick, period=self._period)
        trade_list = self._trades[channel]
        for trade in trades:
            trade_list.append(trade)
