from api.model.asset import Asset
from api.model.position import Position
import copy
from utils import logger
from utils.tools import round_to
from api.model.order import ORDER_ACTION_SELL, ORDER_ACTION_BUY


class BaseStrategyTest:
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
        self.host = ""
        self.mark_wss = ""
        self.wss = ""
        self.access_key = ""
        self.secret_key = ""
        self.test = ""

        self.klines_max_size = 500
        self.depths_max_size = 10
        self.trades_max_size = 10

        self.symbol = "BTC"
        self.mark_symbol = "BTC-USDT"
        self.trade_symbol = "BTC-USDT"
        self.period = "5min"
        self.step = "step2"
        self.lever_rate = 75
        self.price_tick = 0.001
        self.price_offset = 0.0002
        self.loop_interval = 5
        self.auto_curb = False
        self.trading_curb = "none"
        self.long_position_weight_rate = 1
        self.short_position_weight_rate = 1
        self.long_fixed_position = 0
        self.short_fixed_position = 0
        self.fee_rate = 0.002

        # 市场数据
        self.klines = {}
        self.depths = {}
        self.trades = {}

        # 账号数据
        self.assets = Asset()
        self.position = Position(symbol= self.symbol + '/' + self.trade_symbol, long_quantity= 0, short_quantity= 0)

        self.trade_money = 1  # 10USDT.  每次交易的金额, 修改成自己下单的金额.
        self.min_volume = 1  # 最小的交易数量(张).
        self.short_trade_size = 0
        self.long_trade_size = 0
        self.last_price = 0
        self.long_status = 0  # 0不处理  1做多 -1平多
        self.short_status = 0  # 0不处理  1做空 -1 平空

    def update_data(self, data):
        pass

    def on_ticker(self):
        before_state = self.before_strategy()
        if not before_state:  # 策略之前执行
            return
        self.strategy_handle()  # 策略计算
        self.after_strategy()   # 策略之后执行

    def before_strategy(self):
        self.long_status = 0
        self.short_status = 0
        self.long_trade_size = 0
        self.short_trade_size = 0
        self.last_price = 0
        return True

    def strategy_handle(self):
        """
        策略重写
        :return:
        """
        pass

    def after_strategy(self):
        """
        下单或者平仓
        :return:
        """
        # 判断装填和数量是否相等
        if self.long_status == 1 and self.long_trade_size < self.min_volume:
            self.long_status = 0
            self.long_trade_size = 0
        if self.short_status == 1 and self.short_trade_size < self.min_volume:
            self.short_status = 0
            self.short_trade_size = 0
        if self.long_status == 0 and self.short_status == 0:
            return
        self.long_trade_size = self.long_trade_size * self.long_position_weight_rate
        self.short_trade_size = self.short_trade_size * self.short_position_weight_rate
        position = copy.copy(self.position)
        if self.long_status == 1:  # 开多
            if self.long_trade_size > position.long_quantity:   # 开多加仓
                amount = self.long_trade_size - position.long_quantity
                if amount >= self.min_volume:
                    price = self.last_price * (1 + self.price_offset)
                    price = round_to(price, self.price_tick)
                    ret = self.create_order(action=ORDER_ACTION_BUY,  price=price, quantity=amount)

            elif self.long_trade_size < position.long_quantity:  # 开多减仓
                amount = position.long_quantity - self.long_trade_size
                if abs(amount) >= self.min_volume:
                    price = self.last_price * (1 - self.price_offset)
                    price = round_to(price, self.price_tick)
                    ret = self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=amount)

        if self.short_status == 1:  # 开空
            if self.short_trade_size > position.short_quantity:  # 开空加仓
                amount = self.short_trade_size - position.short_quantity
                if amount >= self.min_volume:
                    price = self.last_price * (1 - self.price_offset)
                    price = round_to(price, self.price_tick)
                    ret = self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=-amount)

            elif self.short_trade_size < position.short_quantity:  # 开空减仓
                amount = position.short_quantity - self.short_trade_size
                if abs(amount) >= self.min_volume:
                    price = self.last_price * (1 + self.price_offset)
                    price = round_to(price, self.price_tick)
                    ret = self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=-amount)

        if self.long_status == -1:  # 平多
            if position.long_quantity > 0:
                price = self.last_price * (1 - self.price_offset)
                price = round_to(price, self.price_tick)
                ret = self.create_order(action=ORDER_ACTION_SELL, price=price, quantity=position.long_quantity)

        if self.short_status == -1:  # 平空
            if position.short_quantity > 0:
                price = self.last_price * (1 + self.price_offset)
                price = round_to(price, self.price_tick)
                ret = self.create_order(action=ORDER_ACTION_BUY, price=price, quantity=-position.short_quantity)

    def create_order(self, action, price, quantity):
        if action == ORDER_ACTION_BUY:
            if quantity > 0:
                self.position.long_quantity = self.position.long_quantity + quantity
                logger.info("开多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate,
                            caller=self)
                print("开多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate)
            elif quantity < 0:
                self.position.short_quantity = self.position.short_quantity + quantity
                logger.info("平空 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate,
                            caller=self)
                print("平空 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate)
        if action == ORDER_ACTION_SELL:
            if quantity > 0:
                self.position.long_quantity = self.position.long_quantity - quantity
                logger.info("平多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate,
                            caller=self)
                print("平多 price:", price, "amount:", self.position.long_quantity, "rate:", self.lever_rate)
            elif quantity < 0:
                self.position.short_quantity = self.position.short_quantity - quantity
                logger.info("开空 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate,
                            caller=self)
                print("开空 price:", price, "amount:", self.position.short_quantity, "rate:", self.lever_rate)
        return 0





