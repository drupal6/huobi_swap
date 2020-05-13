# -*- coding:utf-8 -*-

"""
Trade Module.

"""

import copy

from api.model import const
from api.model.error import Error
from utils import logger
from utils import tools
from api.model.tasks import SingleTask
from api.model.order import ORDER_TYPE_LIMIT
from api.model.order import Order
from api.model.position import Position
from api.huobi.huobi_trade import HuobiTrade
from api.model.asset import Asset
from api.huobi.sub.base_sub import BaseSub
from api.huobi.sub.asset_sub import AssetSub
from api.huobi.sub.init_asset_sub import InitAssetSub
from api.huobi.sub.position_sub import PositonSub
from api.huobi.sub.init_position_sub import InitPositonSub
from api.huobi.sub.order_sub import OrderSub
from api.model.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL
from api.model.order import ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET, ORDER_TYPE_MAKER, ORDER_TYPE_FOK, ORDER_TYPE_IOC


class Trade:

    def __init__(self, platform="", wss=None, access_key=None, secret_key=None, rest_api=None):
        """initialize trade object."""
        self._platform = platform
        self._rest_api = rest_api
        self._wss = wss
        self._access_key = access_key
        self._secret_key = secret_key
        self._channel_sub = {}
        self._t = None

    def start(self):
        tt = {
            "platform": self._platform,
            "wss": self._wss,
            "access_key": self._access_key,
            "secret_key": self._secret_key,
            "process_binary": self.process_binary,
        }
        self._t = HuobiTrade(**tt)

    def add_sub(self, sub: BaseSub):
        self._channel_sub[sub.ch().lower()] = sub

    async def auth_call_back(self, data):
        if data["err-code"] != 0:
            e = Error("Websocket connection authorized failed: {}".format(data))
            logger.error(e, caller=self)
            return
        for sub in self._channel_sub.values():
            await self._t.add_sub(sub)

    async def sub_callback(self, data):
        pass
        # if data["err-code"] != 0:
        #     e = Error("subscribe {} failed!".format(data["topic"]))
        #     logger.error(e, caller=self)
        #     SingleTask.run(self._init_success_callback, False, e)
        #     return
        # topic = data["topic"]
        # sub = self._channel_sub[topic]
        # if isinstance(sub, AssetSub):
        #     success, error = await self._rest_api.get_asset_info(sub.symbol())
        #     if error:
        #         e = Error("get asset failed!")
        #         SingleTask.run(self._init_success_callback, False, e)
        #     for order_info in success["data"]["orders"]:
        #         order_info["ts"] = order_info["created_at"]
        #         self._update_order(order_info)
        #     SingleTask.run(self._init_success_callback, True, None)
        # elif isinstance(sub, OrderSub):
        #     success, error = await self._rest_api.get_open_orders(sub.symbol())
        #     if error:
        #         e = Error("get open orders failed!")
        #         SingleTask.run(self._init_success_callback, False, e)
        #     for order_info in success["data"]["orders"]:
        #         order_info["ts"] = order_info["created_at"]
        #         self._update_order(order_info)
        #     SingleTask.run(self._init_success_callback, True, None)
        # elif isinstance(sub, PositonSub):
        #     success, error = await self.get_position(self.sub.symbol())
        #     if error:
        #         e = Error("get position failed!")
        #         SingleTask.run(self._init_success_callback, False, e)
        #     for order_info in success["data"]["orders"]:
        #         order_info["ts"] = order_info["created_at"]
        #         self._update_order(order_info)
        #     SingleTask.run(self._init_success_callback, True, None)
        # else:
        #     pass

    async def process_binary(self, op, data):
        if op == "auth":
            await self.auth_call_back(data)
        elif op == "sub":
            await self.sub_callback(data)
        elif op == "notify":
            topic = data["topic"]
            sub = self._channel_sub.get(topic.lower(), None)
            if sub:
                await sub.call_back(topic, data)
            else:

                logger.error("event error! topic:", topic, "data:", data, caller=self)

    async def create_order(self, symbol, contract_type, action, price, quantity, order_type=ORDER_TYPE_LIMIT, **kwargs):
        """ Create an order.
        Args:
            symbol:交割合约"BTC","ETH"...
            symbol:永久合约"BTC-USD"...
            contract_type:合约类型 ("this_week":当周 "next_week":下周 "quarter":季度)
            action: Trade direction, `BUY` or `SELL`.
            price: Price of each contract.
            quantity: The buying or selling quantity.
            order_type: Specific type of order, `LIMIT` or `MARKET`. (default is `LIMIT`)

        Returns:
            order_no: Order ID if created successfully, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        if int(quantity) > 0:
            if action == ORDER_ACTION_BUY:
                direction = "buy"
                offset = "open"
            elif action == ORDER_ACTION_SELL:
                direction = "sell"
                offset = "close"
            else:
                logger.error("action error1", caller=self)
                return None, "action error"
        else:
            if action == ORDER_ACTION_BUY:
                direction = "buy"
                offset = "close"
            elif action == ORDER_ACTION_SELL:
                direction = "sell"
                offset = "open"
            else:
                logger.error("action error2", caller=self)
                return None, "action error"

        lever_rate = kwargs.get("lever_rate", 50)
        if order_type == ORDER_TYPE_LIMIT:
            order_price_type = "limit"
        elif order_type == ORDER_TYPE_MARKET:
            order_price_type = "lightning"
        elif order_type == ORDER_TYPE_MAKER:
            order_price_type = "post_only"
        elif order_type == ORDER_TYPE_FOK:
            order_price_type = "fok"
        elif order_type == ORDER_TYPE_IOC:
            order_price_type = "ioc"
        else:
            logger.error("order type error", caller=self)
            return None, "order type error"

        quantity = abs(int(quantity))
        if self._platform == "swap":
            result, error = await self._rest_api.create_order(contract_code=symbol, quantity=quantity,
                                                              direction=direction, offset=offset, lever_rate=lever_rate,
                                                              order_price_type=order_price_type, price=price)
        else:
            result, error = await self._rest_api.create_order(symbol=symbol, contract_type=contract_type,
                                                              contract_code="", volume=quantity, direction=direction,
                                                              offset=offset, lever_rate=lever_rate,
                                                              order_price_type=order_price_type, price=price)
        if error:
            logger.error("create_order error! error:", error, caller=self)
            return None, error
        print(str(result["data"]["order_id"]))
        return str(result["data"]["order_id"]), None
    
    async def create_orders(self, symbol, orders_data, **kwargs):
        """ Create batch order
        Returns:
            symbol:"BTC","ETH"...
            orders_no:
            error: error information.
        """
        orders_data = []
        for order in orders_data:
            if int(order["quantity"]) > 0:
                if order["action"] == ORDER_ACTION_BUY:
                    direction = "buy"
                    offset = "open"
                elif order["action"] == ORDER_ACTION_SELL:
                    direction = "sell"
                    offset = "close"
                else:
                    return None, "action error"
            else:
                if order["action"] == ORDER_ACTION_BUY:
                    direction = "buy"
                    offset = "close"
                elif order["action"] == ORDER_ACTION_SELL:
                    direction = "sell"
                    offset = "open"
                else:
                    return None, "action error"

            lever_rate = order["lever_rate"]
            if order["order_type"] == ORDER_TYPE_LIMIT:
                order_price_type = "limit"
            elif order["order_type"] == ORDER_TYPE_MARKET:
                order_price_type = "optimal_20"
            elif order["order_type"] == ORDER_TYPE_MAKER:
                order_price_type = "post_only"
            elif order_price_type == ORDER_TYPE_FOK:
                order_price_type = "fok"
            elif order_price_type == ORDER_TYPE_IOC:
                order_price_type = "ioc"
            else:
                return None, "order type error"

            quantity = abs(int(order["quantity"]))

            client_order_id = order.get("client_order_id", "")

            orders_data.append({"contract_code": symbol,
                                "client_order_id": client_order_id, "price": order["price"], "volume": quantity,
                                "direction": direction, "offset": offset,
                                "leverRate": lever_rate, "orderPriceType": order_price_type})

        result, error = await self._rest_api.create_orders({"orders_data": orders_data})
        if error:
            return None, error
        order_nos = [order["order_id"] for order in result.get("data").get("success")]
        return order_nos, result.get("data").get("errors")

    async def revoke_order(self, symbol, contract_type, *order_nos):
        """ Revoke (an) order(s).
        Args:
             symbol:交割合约"BTC","ETH"...
             symbol:永久合约"BTC-USD"...
            contract_type:合约类型 ("this_week":当周 "next_week":下周 "quarter":季度)
            order_nos: Order id list, you can set this param to 0 or multiple items. If you set 0 param, you can cancel
                all orders for this symbol(initialized in Trade object). If you set 1 param, you can cancel an order.
                If you set multiple param, you can cancel multiple orders. Do not set param length more than 100.

        Returns:
            success: If execute successfully, return success information, otherwise it's None.
            error: If execute failed, return error information, otherwise it's None.
        """
        # If len(order_nos) == 0, you will cancel all orders for this symbol(initialized in Trade object).
        if len(order_nos) == 0:
            if self._platform == "swap":
                success, error = await self._rest_api.revoke_order_all(symbol)
            else:
                success, error = await self._rest_api.revoke_order_all(symbol, '', contract_type)
            if error:
                return False, error
            if success.get("errors"):
                return False, success["errors"]
            return True, None

        # If len(order_nos) == 1, you will cancel an order.
        if len(order_nos) == 1:
            success, error = await self._rest_api.revoke_orders(symbol, order_nos[0])
            if error:
                return order_nos[0], error
            if success.get("errors"):
                return False, success["errors"]
            else:
                return order_nos[0], None

        # If len(order_nos) > 1, you will cancel multiple orders.
        if len(order_nos) > 1:
            success, error = await self._rest_api.revoke_orders(symbol, order_nos)
            if error:
                return order_nos[0], error
            if success.get("errors"):
                return False, success["errors"]
            return success, error

