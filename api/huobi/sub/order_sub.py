from api.huobi.sub.base_sub import BaseSub
from utils import logger
from utils import tools
from utils.dingding_msg_util import MsgUtil
from api.model.order import Order
from api.model.order import ORDER_ACTION_SELL, ORDER_ACTION_BUY
from api.model.order import TRADE_TYPE_BUY_CLOSE, TRADE_TYPE_BUY_OPEN, TRADE_TYPE_SELL_CLOSE, TRADE_TYPE_SELL_OPEN
from api.model.order import ORDER_STATUS_CANCELED, ORDER_STATUS_SUBMITTED, ORDER_STATUS_FAILED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_PARTIAL_FILLED


class OrderSub(BaseSub):
    """
    订单订阅
    """

    def __init__(self, platform, symbol, contract_type, orders):
        """
        symbol:交割合约btc、bch
        contract_type当周:"this_week", 次周:"next_week", 季度:"quarter"
        symbol:永续合约BTC
        contract_type续合约:"BTC-USD"
        """
        self._platform = platform
        self._symbol = symbol
        self._orders = orders
        self._contract_type = contract_type
        if self._platform == "swap":
            self._ch = "orders.{symbol}".format(symbol=self._contract_type)
        else:
            self._ch = "orders.{symbol}".format(symbol=self._symbol)

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

    async def call_back(self, channel, order_info):
        print(order_info)
        if order_info["symbol"] != self._symbol.upper():
            return
        if self._platform == "swap":
            if order_info["contract_code"] != self._contract_type:
                return
        else:
            if order_info["contract_type"] != self._contract_type:
                return
        order_no = str(order_info["order_id"])
        status = order_info["status"]

        order = self._orders.get(order_no)
        if not order:
            if order_info["direction"] == "buy":
                if order_info["offset"] == "open":
                    trade_type = TRADE_TYPE_BUY_OPEN
                else:
                    trade_type = TRADE_TYPE_BUY_CLOSE
            else:
                if order_info["offset"] == "close":
                    trade_type = TRADE_TYPE_SELL_CLOSE
                else:
                    trade_type = TRADE_TYPE_SELL_OPEN

            info = {
                "order_no": order_no,
                "action": ORDER_ACTION_BUY if order_info["direction"] == "buy" else ORDER_ACTION_SELL,
                "symbol": self._symbol + '/' + self._contract_type,
                "price": order_info["price"],
                "quantity": order_info["volume"],
                "trade_type": trade_type
            }
            order = Order(**info)
            self._orders[order_no] = order

        if status in [1, 2, 3]:
            order.status = ORDER_STATUS_SUBMITTED
        elif status == 4:
            order.status = ORDER_STATUS_PARTIAL_FILLED
            order.remain = int(order.quantity) - int(order_info["trade_volume"])
        elif status == 6:
            order.status = ORDER_STATUS_FILLED
            order.remain = 0
        elif status in [5, 7]:
            order.status = ORDER_STATUS_CANCELED
            order.remain = int(order.quantity) - int(order_info["trade_volume"])
        else:
            return

        order.avg_price = order_info["trade_avg_price"]
        order.ctime = order_info["created_at"]
        order.utime = order_info["ts"]
        # Delete order that already completed.
        if order.status in [ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED]:
            self._orders.pop(order_no)

        # publish order
        MsgUtil.order_msg(order_info)
        logger.info("symbol:", order.symbol, "order:", order, caller=self)
