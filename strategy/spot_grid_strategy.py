from api.huobi.huobi_request_spot import HuobiRequestSpot
from utils.tools import round_to
import datetime
from enum import Enum
from api.model.tasks import LoopRunTask
from utils.config import config
from utils import logger


class OrderStatus(Enum):
    SUBMITTED = "submitted"  # 已提交
    PARTIALFILLED = "partial-filled"  # 部分成交
    PARTIALCANCELED = "partial-canceled"  # 部分成交撤销,
    FILLED = "filled"  # 完全成交
    CANCELED = "canceled"  # 已撤销
    CREATED = "created"  # 已提交


class OrderType(Enum):
    BUYMARKET = "buy-market"
    SELLMARKET = "sell-market"
    BUYLIMIT = "buy-limit"
    SELLLIMIT = "sell-limit"
    BUYIOC = "buy-ioc"
    SELLIOC = " sell-ioc"
    BUYLIMITMAKER = "buy-limit-maker"
    SELLLIMITMAKER = "sell-limit-maker"
    BUYSTOPLIMIT = "buy-stop-limit"
    SELLSTOPLIMIT = "sell-stop-limit"
    BUYLIMITFOK = "buy-limit-fok"
    SELLLIMITFOK = "sell-limit-fok"
    BUYSTOPLIMITFOK = "buy-stop-limit-fok"
    SELLSTOPLIMITFOK = "sell-stop-limit-fok"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class SpotGridStrategy(object):

    def __init__(self):
        self.host = config.accounts.get("host", "https://api.huobi.pro")
        self.access_key = config.accounts.get("access_key")
        self.secret_key = config.accounts.get("secret_key")
        self.symbol = config.markets.get("mark_symbol")
        self.platform = config.markets.get("platform", "spot")
        self.base_symbol = config.markets.get("base_symbol")
        self.quote_symbol = config.markets.get("quote_symbol")
        self.gap_percent = config.markets.get("gap_percent", 0.003)  # 网格大小
        self.quantity = config.markets.get("quantity", 1)   # 成交量
        self.quantity_rate = config.markets.get("quantity_rate", 1)   #
        self.min_price = config.markets.get("min_price", 0.0001)  # 价格保留小数位
        # self.min_qty = 0.01  # 数量保留小数位
        self.max_orders = config.markets.get("max_orders", 1)
        self.http_client = HuobiRequestSpot(host=self.host, access_key=self.access_key, secret_key=self.secret_key)
        self.buy_orders = []  # 买单
        self.sell_orders = []  # 卖单
        self.account_id = None

        LoopRunTask.register(self.grid_trader, 50)

    async def init_data(self):
        success, error = await self.http_client.get_accounts()
        if error:
            logger.error("init account_id error. error:", error, caller=self)
            exit(0)
        if success.get("status") == "ok":
            data = success.get("data")
            for d in data:
                if d.get("type") == self.platform:
                    self.account_id = d.get("id")
        if not self.account_id:
            logger.error("init account_id error. error:", success, caller=self)
            exit(0)
        order_data, error = await self.http_client.get_open_orders(account_id=self.account_id, symbol=self.symbol)
        if error:
            logger.error("init get_open_orders error. msg:", error, caller=self)
        if order_data:
            open_orders = order_data.get("data")
            for order in open_orders:
                if order.get("type") == "buy-limit":
                    self.buy_orders.append(order)
                elif order.get("type") == "sell-limit":
                    self.sell_orders.append(order)
        symbols_data, err = await self.http_client.get_symbols()
        if err:
            logger.error("get_symbols error. error:", err, caller=self)
        if symbols_data:
            symbols = symbols_data.get("data")
            for symbol_info in symbols:
                if symbol_info["symbol"] == self.symbol:
                    bid_price, ask_price = await self.get_bid_ask_price()
                    min_order_value = symbol_info["min-order-value"]
                    min_order_amt = symbol_info["min-order-amt"]
                    self.quantity = (round_to(min_order_value / ask_price, min_order_amt) + min_order_amt * 2) * self.quantity_rate
                    self.min_price = 1 / (10 ** symbol_info["price-precision"])

    async def get_bid_ask_price(self):
        ticker, error = await self.http_client.get_ticker(self.symbol)
        bid_price = 0
        ask_price = 0
        if error:
            logger.error("init get_bid_ask_price error. error:", error, caller=self)
            return
        if ticker.get("status") == "ok":
            data = ticker.get("tick")
            if data:
                bid_price = float(data.get('bid', [0, 0])[0])
                ask_price = float(data.get('ask', [0, 0])[0])
        else:
            logger.error("get_ticker error.", ticker, caller=self)
        return bid_price, ask_price

    async def grid_trader(self, *args, **kwargs):
        """
        执行核心逻辑，网格交易的逻辑.
        :return:
        """
        if not self.account_id:
            await self.init_data()
        bid_price, ask_price = await self.get_bid_ask_price()

        quantity = self.quantity

        self.buy_orders.sort(key=lambda x: float(x['price']), reverse=True)  # 最高价到最低价.
        self.sell_orders.sort(key=lambda x: float(x['price']), reverse=True)  # 最高价到最低价.

        buy_delete_orders = []  # 需要删除买单
        sell_delete_orders = []  # 需要删除的卖单
        balance = await self.get_balance()

        # 买单逻辑,检查成交的情况.
        for buy_order in self.buy_orders:
            check_order, error = await self.http_client.get_order(buy_order.get("id"))
            if check_order:
                if check_order.get("status") != "ok":
                    buy_delete_orders.append(buy_order)
                order_data = check_order.get("data")
                if order_data.get('state') == OrderStatus.CANCELED.value:
                    buy_delete_orders.append(buy_order)
                elif order_data.get('state') == OrderStatus.FILLED.value:
                    # 买单成交，挂卖单.
                    sell_price = round_to(float(order_data.get("price")) * (1 + float(self.gap_percent)), float(self.min_price))
                    if 0 < sell_price < ask_price:
                        # 防止价格
                        sell_price = round_to(ask_price, float(self.min_price))
                    new_sell_order = await self.place_order(balance=balance, type=OrderType.SELLLIMIT, amount=quantity, price=sell_price)
                    if new_sell_order:
                        buy_delete_orders.append(buy_order)
                        self.sell_orders.append(new_sell_order)
                    buy_price = round_to(float(order_data.get("price")) * (1 - float(self.gap_percent)), self.min_price)
                    if buy_price > bid_price > 0:
                        buy_price = round_to(buy_price, float(self.min_price))
                    new_buy_order = await self.place_order(balance=balance, type=OrderType.BUYLIMIT, amount=quantity, price=buy_price)
                    if new_buy_order:
                        self.buy_orders.append(new_buy_order)
                elif order_data.get('state') == OrderStatus.SUBMITTED.value or order_data.get('state') == OrderStatus.CREATED.value:
                    print("buy order status is: New")
                else:
                    print(f"buy order status is not above options: {order_data.get('state')}")

        # 过期或者拒绝的订单删除掉.
        for delete_order in buy_delete_orders:
            self.buy_orders.remove(delete_order)

        # 卖单逻辑, 检查卖单成交情况.
        for sell_order in self.sell_orders:
            check_order, error = await self.http_client.get_order(sell_order.get('id'))
            if check_order:
                if check_order.get("status") != "ok":
                    sell_delete_orders.append(sell_order)
                order_data = check_order.get("data")
                if order_data.get('state') == OrderStatus.CANCELED.value:
                    sell_delete_orders.append(sell_order)
                elif order_data.get('state') == OrderStatus.FILLED.value:
                    # 卖单成交，先下买单.
                    buy_price = round_to(float(order_data.get("price")) * (1 - float(self.gap_percent)), float(self.min_price))
                    if buy_price > bid_price > 0:
                        buy_price = round_to(buy_price, float(self.min_price))
                    new_buy_order = await self.place_order(balance=balance, type=OrderType.BUYLIMIT, amount=quantity, price=buy_price)
                    if new_buy_order:
                        sell_delete_orders.append(sell_order)
                        self.buy_orders.append(new_buy_order)

                    sell_price = round_to(float(order_data.get("price")) * (1 + float(self.gap_percent)), float(self.min_price))
                    if 0 < sell_price < ask_price:
                        # 防止价格
                        sell_price = round_to(ask_price, float(self.min_price))
                    new_sell_order = await self.place_order(balance=balance, type=OrderType.SELLLIMIT, amount=quantity, price=sell_price)
                    if new_sell_order:
                        self.sell_orders.append(new_sell_order)

                elif order_data.get('state') == OrderStatus.SUBMITTED.value or order_data.get('state') == OrderStatus.CREATED.value:
                    print("sell order status is: New")
                else:
                    print(f"sell order status is not in above options: {order_data.get('state')}")

        # 过期或者拒绝的订单删除掉.
        for delete_order in sell_delete_orders:
            self.sell_orders.remove(delete_order)

        # 没有买单的时候.
        if len(self.buy_orders) <= 0:
            if bid_price > 0:
                price = round_to(bid_price * (1 - float(self.gap_percent)), float(self.min_price))
                buy_order = await self.place_order(balance=balance, type=OrderType.BUYLIMIT, amount=quantity, price=price)
                if buy_order:
                    self.buy_orders.append(buy_order)
        elif len(self.buy_orders) > int(self.max_orders): # 最多允许的挂单数量.
            # 订单数量比较多的时候.
            self.buy_orders.sort(key=lambda x: float(x['price']), reverse=False)  # 最低价到最高价
            delete_order = self.buy_orders[0]
            order, error = await self.http_client.cancel_order(delete_order.get('id'))
            if order:
                self.buy_orders.remove(delete_order)

        # 没有卖单的时候.
        if len(self.sell_orders) <= 0:
            if ask_price > 0:
                price = round_to(ask_price * (1 + float(self.gap_percent)), float(self.min_price))
                order = await self.place_order(balance=balance, type=OrderType.SELLLIMIT, amount=quantity, price=price)
                if order:
                    self.sell_orders.append(order)
        elif len(self.sell_orders) > int(self.max_orders):  # 最多允许的挂单数量.
            # 订单数量比较多的时候.
            self.sell_orders.sort(key=lambda x: x['price'], reverse=True)  # 最高价到最低价
            delete_order = self.sell_orders[0]
            order, error = await self.http_client.cancel_order(delete_order.get('id'))
            if order:
                self.sell_orders.remove(delete_order)

    async def place_order(self, balance, type, amount, price):
        if balance is None:
            logger.error("balance is none", caller=self)
            return
        if type == OrderType.SELLLIMIT:
            if balance[self.base_symbol]["trade"] < amount:
                logger.info("sell place_order interrupt " + self.base_symbol + " not enouth", balance[self.base_symbol]["trade"], amount, caller=self)
                return
        if type == OrderType.BUYLIMIT:
            if balance[self.quote_symbol]["trade"] < amount * price:
                logger.info("buy place_order interrupt " + self.quote_symbol + " not enouth", balance[self.quote_symbol]["trade"], amount, caller=self)
                return
        success, error = await self.http_client.place_order(account_id=self.account_id, symbol=self.symbol, type=type.value, amount=amount, price=price)
        if error:
            logger.error("place_order error. error:", error, caller=self)
        if success:
            if success.get("data"):
                order, error1 = await self.http_client.get_order(success.get("data"))
                if error1:
                    logger.error("get_order error. error:", error, caller=self)
                if order:
                    return order.get("data")
        return None

    async def get_balance(self):
        success, error = await self.http_client.get_balance(self.account_id)
        if error:
            logger.error("get_balance error. error:", error, caller=self)
            return None
        base_balance = {"trade": 0, "frozen": 0}
        quoto_balance = {"trade": 0, "frozen": 0}
        if success:
            if success.get("status") == "ok":
                base_balance = {}
                quoto_balance = {}
                balance_list = success.get("data").get("list")
                for balance in balance_list:
                    if balance["currency"] == self.base_symbol:
                        base_balance[balance["type"]] = float(balance["balance"])
                    if balance["currency"] == self.quote_symbol:
                        quoto_balance[balance["type"]] = float(balance["balance"])
        return {
            self.base_symbol: base_balance,
            self.quote_symbol: quoto_balance
        }
