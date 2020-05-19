from api.model.market import Market
from api.huobi.huobi_request import HuobiRequest
from api.huobi.huobi_request_swap import HuobiSwapRequest
from api.model.tasks import LoopRunTask
from api.huobi.sub.init_kline_sub import InitKlineSub
from api.huobi.sub.kline_sub import KlineSub
from api.huobi.sub.depth_sub import DepthSub
from api.huobi.sub.trade_sub import TradeSub
from api.huobi.sub.asset_sub import AssetSub
from api.huobi.sub.position_sub import PositonSub
from api.huobi.sub.order_sub import OrderSub
from api.huobi.sub.init_order_sub import InitOrderSub
from api.huobi.sub.init_asset_sub import InitAssetSub
from api.huobi.sub.init_position_sub import InitPositonSub
from api.model.trade import Trade
from api.model.asset import Asset
from api.model.position import Position
import copy
from utils import tools
from utils.config import config
from utils import logger
from utils.tools import round_to
from api.model.error import Error


class BaseStrategy:
    """
    基础策略类
    交割合约：
    "symbol": "eth",
    "mark_symbol": "ETH_CQ",
    "trade_symbol": "quarter",
    永久合约：
    "symbol": "ETH",
    "mark_symbol": "ETH_USD",
    "trade_symbol": "ETH_USD",
    2者的差别有：
    资产、下单、撤单中的symbol不一样
    """

    def __init__(self):
        self.host = config.accounts.get("host")
        self.mark_wss = config.accounts.get("mark_wss")
        self.wss = config.accounts.get("trade_wss")
        self.access_key = config.accounts.get("access_key")
        self.secret_key = config.accounts.get("secret_key")
        self.test = config.accounts.get("is_test", True)

        self.klines_max_size = config.markets.get("klines_max_size")
        self.depths_max_size = config.markets.get("depths_max_size")
        self.trades_max_size = config.markets.get("trades_max_size")

        self.symbol = config.markets.get("symbol")
        self.mark_symbol = config.markets.get("mark_symbol")
        self.trade_symbol = config.markets.get("trade_symbol")
        self.period = config.markets.get("period")
        self.step = config.markets.get("step")
        self.lever_rate = config.markets.get("lever_rate")
        self.price_tick = config.markets.get("price_tick")
        self.price_offset = config.markets.get("price_offset")
        self.loop_interval = config.markets.get("loop_interval")
        self.order_cancel_time = config.markets.get("order_cancel_time")
        self.trading_curb = config.markets.get("trading_curb")
        self.long_position_weight_rate = config.markets.get("long_position_weight_rate")
        self.short_position_weight_rate = config.markets.get("short_position_weight_rate")
        self.platform = config.markets.get("platform")

        e = None
        if not self.host:
            e = Error("host miss")
        if not self.mark_wss:
            e = Error("mark_wss miss")
        if not self.wss:
            e = Error("trade_wss miss")
        if not self.access_key:
            e = Error("access_key miss")
        if not self.secret_key:
            e = Error("secret_key miss")

        if not self.platform:
            e = Error("platform miss")
        if not self.klines_max_size:
            e = Error("klines_max_size miss")
        if not self.depths_max_size:
            e = Error("depths_max_size miss")
        if not self.trades_max_size:
            e = Error("trades_max_size miss")

        if not self.symbol:
            e = Error("symbol miss")
        if not self.mark_symbol:
            e = Error("mark_symbol miss")
        if not self.trade_symbol:
            e = Error("trade_symbol miss")
        if not self.period:
            e = Error("period miss")
        if not self.step:
            e = Error("step miss")
        if not self.lever_rate:
            e = Error("lever_rate miss")
        if not self.price_tick:
            e = Error("price_tick miss")
        if not self.price_offset:
            e = Error("price_offset miss")
        if not self.loop_interval:
            e = Error("loop_interval miss")
        if not self.order_cancel_time:
            e = Error("order_cancel_time miss")
        if not self.trading_curb:
            e = Error("trading_curb miss")
        if not self.long_position_weight_rate:
            e = Error("long_position_weight_rate miss")
        if not self.short_position_weight_rate:
            e = Error("short_position_weight_rate miss")

        if e:
            logger.error(e, caller=self)
            return

        # 市场数据
        self.klines = {}
        self.depths = {}
        self.trades = {}

        # 账号数据
        self.assets = Asset()
        self.orders = {}
        self.position = Position(self.symbol + '/' + self.trade_symbol)

        self.trade_money = 1  # 10USDT.  每次交易的金额, 修改成自己下单的金额.
        self.min_volume = 1  # 最小的交易数量(张).
        self.short_trade_size = 0
        self.long_trade_size = 0
        self.last_price = 0
        self.long_status = 0  # 0不处理  1做多 -1平多
        self.short_status = 0  # 0不处理  1做空 -1 平空
        self.last_order = {}  # 最近下单记录

        # 初始http链接
        if self.platform == "swap":
            self.request = HuobiSwapRequest(host=self.host, access_key=self.access_key, secret_key=self.secret_key)
        else:
            self.request = HuobiRequest(host=self.host, access_key=self.access_key, secret_key=self.secret_key)

        # 初始和监听市场数据
        self.market = Market(platform=self.platform, wss=self.mark_wss, request=self.request)
        self.market.add_sub(InitKlineSub(symbol=self.mark_symbol, period=self.period, klines=self.klines,
                                         request=self.request, klines_max_size=self.klines_max_size))
        self.market.add_sub(KlineSub(symbol=self.mark_symbol, period=self.period, klines=self.klines,
                                     klines_max_size=self.klines_max_size))
        self.market.add_sub(DepthSub(symbol=self.mark_symbol, step=self.step, depths=self.depths,
                                     depths_max_size=self.depths_max_size))
        self.market.add_sub(TradeSub(symbol=self.mark_symbol, trades=self.trades, trades_max_size=self.trades_max_size))
        self.market.start()

        # 初始和监听交易数据
        self.trade = Trade(platform=self.platform, wss=self.wss, access_key=self.access_key, secret_key=self.secret_key,
                           rest_api=self.request)
        self.trade.add_sub(InitPositonSub(platform=self.platform, symbol=self.symbol, contract_type=self.trade_symbol,
                                          position=self.position))
        self.trade.add_sub(PositonSub(platform=self.platform, symbol=self.symbol, contract_type=self.trade_symbol,
                                      position=self.position))
        self.trade.add_sub(InitOrderSub(platform=self.platform, symbol=self.symbol, contract_type=self.trade_symbol,
                                        orders=self.orders,
                                        request=self.request))
        self.trade.add_sub(OrderSub(platform=self.platform, symbol=self.symbol, contract_type=self.trade_symbol, orders=self.orders))
        if self.platform == "swap":
            self.trade.add_sub(InitAssetSub(symbol=self.trade_symbol, asset=self.assets))
            self.trade.add_sub(AssetSub(symbol=self.trade_symbol, asset=self.assets))
        else:
            self.trade.add_sub(InitAssetSub(symbol=self.symbol, asset=self.assets))
            self.trade.add_sub(AssetSub(symbol=self.symbol, asset=self.assets))

        self.trade.start()
        # 运行周期
        LoopRunTask.register(self.on_ticker, self.loop_interval)

    async def on_ticker(self, *args, **kwargs):
        before_state = await self.before_strategy()
        if not before_state:  # 策略之前执行
            return
        self.strategy_handle()  # 策略计算
        await self.after_strategy()   # 策略之后执行

    async def before_strategy(self):
        # 撤销超过order_cancel_time的挂单
        orders = copy.copy(self.orders)
        ut_time = tools.get_cur_timestamp_ms()
        if len(orders) > 0:
            for no in orders.values():
                if ut_time >= no.ctime + self.order_cancel_time:
                    print("取消订单", ut_time, no.ctime, self.order_cancel_time)
                    if self.platform == "swap":
                        await self.trade.revoke_order(self.trade_symbol.upper(), self.trade_symbol, no.order_no)
                    else:
                        await self.trade.revoke_order(self.symbol.upper(), self.trade_symbol, no.order_no)

        if len(self.klines) == 0:  # k线数据没有
            return False
        if len(self.trades) == 0:  # 最近成交记录没有
            return False
        if not self.position.init:
            return False

        # 设置计算参数
        self.long_status = 0
        self.short_status = 0
        self.long_trade_size = 0
        self.short_trade_size = 0
        self.last_price = 0
        # 获取最近成交的价格
        trades = copy.copy(self.trades)
        last_trades = trades.get("market." + self.mark_symbol + ".trade.detail")
        if last_trades and len(last_trades) > 0:
            self.last_price = round_to(float(last_trades[-1].price), self.price_tick)
        if self.last_price <= 0:  # 最近一次的成交价格没有
            return False
        return True

    def strategy_handle(self):
        """
        策略重写
        :return:
        """
        pass

    async def after_strategy(self):
        """
        下单或者平仓
        :return:
        """
        orders = copy.copy(self.orders)
        if len(orders) > 0:
            return

        # 判断装填和数量是否相等
        if self.long_status == 0 and self.short_status == 0:
            return
        if self.long_status == 1 and self.long_trade_size < self.min_volume:
            return
        if self.short_status == 1 and self.short_trade_size < self.min_volume:
            return

        position = copy.copy(self.position)
        if self.long_status == 1 and self.trading_curb != "short":  # 开多
            if self.long_trade_size > position.long_quantity:   # 开多加仓
                amount = self.long_trade_size - position.long_quantity
                if amount >= self.min_volume:
                    price = self.last_price * (1 + self.price_offset)
                    price = round_to(price, self.price_tick)
                    logger.info("开多加仓 price:", price, "amount:", amount, "rate:", self.lever_rate, caller=self)
                    await self.create_order(action="BUY",  price=price, quantity=amount)

            elif self.long_trade_size < position.long_quantity:  # 开多减仓
                amount = position.long_quantity - self.long_trade_size
                if abs(amount) >= self.min_volume:
                    price = self.last_price * (1 - self.price_offset)
                    price = round_to(price, self.price_tick)
                    logger.info("开多减仓 price:", price, "amount:", amount, "rate:", self.lever_rate, caller=self)
                    await self.create_order(action="SELL", price=price, quantity=amount)

        if self.short_status == 1 and self.trading_curb != "long":  # 开空
            if self.short_trade_size > position.short_quantity:  # 开空加仓
                amount = self.short_trade_size - position.short_quantity
                if amount >= self.min_volume:
                    price = self.last_price * (1 - self.price_offset)
                    price = round_to(price, self.price_tick)
                    logger.info("开空加仓 price:", price, "amount:", amount, "rate:", self.lever_rate, caller=self)
                    await self.create_order(action="SELL", price=price, quantity=-amount)

            elif self.short_trade_size < position.short_quantity:  # 开空减仓
                amount = position.short_quantity - self.short_trade_size
                if abs(amount) >= self.min_volume:
                    price = self.last_price * (1 + self.price_offset)
                    price = round_to(price, self.price_tick)
                    logger.info("开空减仓 price:", price, "amount:", "rate:", self.lever_rate, amount, caller=self)
                    await self.create_order(action="BUY", price=price, quantity=-amount)

        if self.long_status == -1:  # 平多
            if position.long_quantity > 0:
                price = self.last_price * (1 - self.price_offset)
                price = round_to(price, self.price_tick)
                logger.info("平多 price:", price, "amount:", position.long_quantity, "rate:", self.lever_rate, caller=self)
                await self.create_order(action="SELL", price=price, quantity=position.long_quantity)

        if self.short_status == -1:  # 平空
            if position.short_quantity > 0:
                price = self.last_price * (1 + self.price_offset)
                price = round_to(price, self.price_tick)
                logger.info("平空 price:", price, "amount:", position.short_quantity, "rate:", self.lever_rate, caller=self)
                await self.create_order(action="BUY", price=price, quantity=-position.short_quantity)

    async def create_order(self, action, price, quantity):
        if not self.test:
            if not self.varify_create_order(action, quantity):
                logger.info("开仓太快 action:", price, " quantity:", quantity, caller=self)
                return
            p = {"lever_rate": self.lever_rate}
            if self.platform == "swap":
                await self.trade.create_order(symbol=self.trade_symbol.upper(), contract_type=self.trade_symbol,
                                              action=action,
                                              price=price, quantity=quantity, **p)
            else:
                await self.trade.create_order(symbol=self.symbol.upper(), contract_type=self.trade_symbol,
                                              action=action,
                                              price=price, quantity=quantity, **p)
        else:
            if action == "BUY":
                if quantity > 0:
                    self.position.long_quantity = self.position.long_quantity + quantity
                    logger.info("开多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate,
                                caller=self)
                elif quantity < 0:
                    self.position.short_quantity = self.position.short_quantity + quantity
                    logger.info("平空 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate,
                                caller=self)
            if action == "SELL":
                if quantity > 0:
                    self.position.long_quantity = self.position.long_quantity - quantity
                    logger.info("平多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate,
                                caller=self)
                elif quantity < 0:
                    self.position.short_quantity = self.position.short_quantity - quantity
                    logger.info("开孔 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate,
                                caller=self)

    def varify_create_order(self, action, quantity):
        """
        检查开多和开空的时间间隔是否太短 5s同一订单不下单
        :param action:
        :param quantity:
        :return:
        """
        ut_time = tools.get_cur_timestamp_ms()
        long_or_short_order = None
        if action == "BUY" and quantity > 0:  # 开多
            long_or_short_order = "long"
        elif action == "SELL" and quantity < 0:  # 开空
            long_or_short_order = "short"
        last__order_info = self.last_order.get(long_or_short_order)
        if last__order_info:
            if last__order_info["action"] == action and last__order_info["quantity"] == quantity and \
                    ut_time < last__order_info["ts"] + 5000:
                return False
        if long_or_short_order:
            last__order_info = {
                "action": action,
                "quantity": quantity,
                "ts": ut_time
            }
            self.last_order[long_or_short_order] = last__order_info
        return True





