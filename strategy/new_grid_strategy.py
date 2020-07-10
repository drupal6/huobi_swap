import copy
from strategy.easy_base_strategy import EasyBaseStrategy
from utils.tools import round_to
from api.model.order import ORDER_ACTION_SELL, ORDER_ACTION_BUY


class NewGridStrategy(EasyBaseStrategy):
    """
    新网格策略
    """

    def __init__(self):
        self.max_orders = 1
        self.atr_per = 0.05   # 最小网格高度要求
        self.same_order_limit = 1  # 同种类型订单数量限制
        super(NewGridStrategy, self).__init__()

    def strategy_handle(self):
        orders = copy.copy(self.orders)
        position = copy.copy(self.position)
        buy_long_orders = []
        buy_short_orders = []
        sell_long_orders = []
        sell_short_orders = []
        for order in orders.values():
            if order["status"] == 5 or order["status"] == 6 or order["status"] == 7:
                continue
            if order["offset"] == "open":
                if order["direction"] == "buy":
                    buy_long_orders.append(order)
                if order["direction"] == "sell":
                    buy_short_orders.append(order)
            if order["offset"] == "close":
                if order["direction"] == "buy":
                    sell_short_orders.append(order)
                if order["direction"] == "sell":
                    sell_long_orders.append(order)
        buy_long_size = len(buy_long_orders)
        buy_short_size = len(buy_short_orders)
        sell_long_size = len(sell_long_orders)
        sell_short_size = len(sell_short_orders)
        bid_price = 0  # 买盘价格
        ask_price = 0  # 买盘价格
        if buy_long_size == 0:
            # 开多单
            price = round_to(bid_price * (1 + self.atr_per), self.price_tick)
            amount = self.min_volume * self.long_position_weight_rate
            await self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=amount)
        elif buy_long_size > self.same_order_limit:
            # 有多个开多单时要留下最小的
            self.buy_long_orders.sort(key=lambda x: float(x.price), reverse=True)  # 最高价到最低价
            for i in range(0, buy_long_size - 1):
                await self.revoke_order(buy_long_orders[i].order_no)

        if buy_short_size == 0:
            # 开空单
            price = round_to(ask_price * (1 - self.atr_per), self.price_tick)
            amount = self.min_volume * self.short_position_weight_rate
            await self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=amount)
        elif buy_short_size > self.same_order_limit:
            # 有多个开空单时要留下最大的
            self.buy_short_orders.sort(key=lambda x: float(x.price), reverse=False)  # 最低价到最高价
            for i in range(0, buy_short_size - 1):
                await self.revoke_order(buy_short_orders[i].order_no)

        if sell_long_size == 0:
            # 平多单
            price = round_to(position.long_avg_open_price * (1 + self.atr_per), self.price_tick)
            amount = -self.min_volume * self.long_position_weight_rate
            await self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=amount)
        elif sell_long_size > self.same_order_limit:
            # 有多个平多单时要留下最小的
            self.sell_long_orders.sort(key=lambda x: float(x.price), reverse=True)  # 最高价到最低价
            for i in range(0, sell_long_size - 1):
                await self.revoke_order(sell_long_orders[i].order_no)

        if sell_short_size == 0:
            # 平空单
            price = round_to(position.short_avg_open_price * (1 - self.atr_per), self.price_tick)
            amount = -self.min_volume * self.long_position_weight_rate
            await self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=amount)
        elif sell_short_size > self.same_order_limit:
            # 有多个平空单时要留下最大的
            self.sell_short_orders.sort(key=lambda x: float(x.price), reverse=False)  # 最低价到最高价
            for i in range(0, sell_short_size - 1):
                await self.revoke_order(sell_short_orders[i].order_no)

