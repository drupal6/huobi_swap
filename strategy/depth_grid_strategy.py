import copy
from strategy.easy_base_strategy import EasyBaseStrategy
from utils.tools import round_to
from api.model.order import ORDER_ACTION_SELL, ORDER_ACTION_BUY
from api.model.order import TRADE_TYPE_BUY_CLOSE, TRADE_TYPE_BUY_OPEN, TRADE_TYPE_SELL_CLOSE, TRADE_TYPE_SELL_OPEN
from api.model.order import ORDER_STATUS_CANCELED, ORDER_STATUS_SUBMITTED, ORDER_STATUS_FAILED, ORDER_STATUS_FILLED, \
    ORDER_STATUS_PARTIAL_FILLED
from utils import logger


class DepthGridStrategy(EasyBaseStrategy):
    """
    新网格策略
    """

    def __init__(self):
        self.max_orders = 1
        self.atr_per = 0.05   # 最小网格高度要求
        self.same_order_limit = 1  # 同种类型订单数量限制
        self.can_user_amount = 0
        super(DepthGridStrategy, self).__init__()

    async def strategy_handle(self):
        if self.contract_size == 0:
            return
        position = copy.copy(self.position)
        orders = copy.copy(self.orders)
        buy_long_orders = []
        buy_short_orders = []
        sell_long_orders = []
        sell_short_orders = []
        for order in orders.values():
            if order.status == ORDER_STATUS_FILLED or order.status == ORDER_STATUS_CANCELED:
                continue
            if order.trade_type == TRADE_TYPE_BUY_OPEN:
                buy_long_orders.append(order)
            if order.trade_type == TRADE_TYPE_SELL_OPEN:
                buy_short_orders.append(order)
            if order.trade_type == TRADE_TYPE_BUY_CLOSE:
                sell_short_orders.append(order)
            if order.trade_type == TRADE_TYPE_SELL_CLOSE:
                sell_long_orders.append(order)
        buy_long_size = len(buy_long_orders)
        buy_short_size = len(buy_short_orders)
        sell_long_size = len(sell_long_orders)
        sell_short_size = len(sell_short_orders)
        ask_price, bid_price = self.ask_bid_price()
        per = self.atr_per / self.lever_rate
        long_amount = self.min_volume * self.long_position_weight_rate
        short_amount = self.min_volume * self.short_position_weight_rate
        self.can_user_amount = self.get_can_user_amoun(bid_price)
        long_quantity = 0
        if position.long_quantity:
            long_quantity = position.long_quantity
        if buy_long_size == 0 and bid_price > 0 and self.can_user_amount >= long_amount > long_quantity:
            # 开多单
            self.can_user_amount = self.can_user_amount - long_amount
            price = round_to(bid_price * (1 - per), self.price_tick)
            await self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=long_amount)
        elif buy_long_size > self.same_order_limit:
            # 有多个开多单时要留下最大的
            self.buy_long_orders.sort(key=lambda x: float(x.price), reverse=False)  # 升序
            for i in range(0, buy_long_size - 1):
                await self.revoke_order(buy_long_orders[i].order_no)

        short_quantity = 0
        if position.short_quantity:
            short_quantity = position.short_quantity
        if buy_short_size == 0 and ask_price > 0 and self.can_user_amount >= short_amount > short_quantity:
            # 开空单
            price = round_to(ask_price * (1 + per), self.price_tick)
            await self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=-short_amount)
        elif buy_short_size > self.same_order_limit:
            # 有多个开空单时要留下最小的
            self.buy_short_orders.sort(key=lambda x: float(x.price), reverse=True)  # 降序
            for i in range(0, buy_short_size - 1):
                await self.revoke_order(buy_short_orders[i].order_no)

        if sell_long_size == 0:
            # 平多单
            if position.long_avg_open_price and position.long_avg_open_price > 0 and position.long_quantity >= long_amount:
                price = max(ask_price, round_to(position.long_avg_open_price * (1 + per), self.price_tick))
                await self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=long_amount)
        elif sell_long_size > self.same_order_limit:
            # 有多个平多单时要留下最小的
            self.sell_long_orders.sort(key=lambda x: float(x.price), reverse=True)  # 降序
            for i in range(0, sell_long_size - 1):
                await self.revoke_order(sell_long_orders[i].order_no)

        if sell_short_size == 0:
            # 平空单
            if position.short_avg_open_price and position.short_avg_open_price > 0 and position.short_quantity >= short_amount:
                price = min(bid_price, round_to(position.short_avg_open_price * (1 - per), self.price_tick))
                await self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=-short_amount)
        elif sell_short_size > self.same_order_limit:
            # 有多个平空单时要留下最大的
            self.sell_short_orders.sort(key=lambda x: float(x.price), reverse=False)  # 升序
            for i in range(0, sell_short_size - 1):
                await self.revoke_order(sell_short_orders[i].order_no)
