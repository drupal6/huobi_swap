from utils import tools
from utils.dingding import DingTalk
from api.model.const import TRADE, KILINE_PERIOD
from collections import deque
from utils.config import config
import copy


class TradeRecordNode:
    def __init__(self, t, symbol):
        self.t = t
        self.symbol = symbol
        self.buy = 0
        self.sell = 0
        self.buy_price = 0
        self.sell_price = 0

    def add(self, direction, quantity, price):
        if direction.lower() == "buy":
            self.buy += quantity
            self.buy_price = price
        elif direction.lower() == "sell":
            self.sell += quantity
            self.sell_price = price

    def __str__(self):
        symbol = self.symbol
        buy = "%.8f" % self.buy
        buy_price = "%.8f" % self.buy_price
        sell = "%.8f" % self.sell
        sell_price = "%.8f" % self.sell_price
        return "%s\nsymbol:%s\nperiod:%s\nbuy:%s\nsell:%s\nbuy price:%s\nsell price:%s" \
               % (self.t, symbol, config.markets.get("period"), buy, sell, buy_price, sell_price)


class Record:

    def __init__(self):
        self.trade_data = deque(maxlen=10)
        self.last_notice_time = 0
        self.notice_period = 10 * 60 * 1000
        self.init = False
        self.period = config.markets.get("period")

    def record_trade(self, symbol, tick, init=False):
        if not self.init and not init:
            return
        if TRADE[self.period] < self.notice_period:
            self.notice_period = TRADE[self.period]
        direction = tick.get("direction")
        quantity = tick.get("amount")
        price = tick.get("price")
        ts = tools.ts_to_datetime_str(int(tick.get("ts") / TRADE[self.period]) * TRADE[self.period] / 1000)

        trn = None
        if len(self.trade_data) > 0:
            trn = self.trade_data[-1]
            if trn.t != ts:
                trn = None
        if not trn:
            trn = TradeRecordNode(ts, symbol)
            self.trade_data.append(trn)
        trn.add(direction, quantity, price)
        self.notice()

    def notice(self):
        notice = True
        if self.last_notice_time > 0:
            ut_time = tools.get_cur_timestamp_ms()
            if self.last_notice_time + self.notice_period > ut_time:
                notice = False
        if not notice:
            return
        self.last_notice_time = tools.get_cur_timestamp_ms()
        trn = self.trade_recode_node()
        if not trn:
            return
        msg = trn.__str__()
        DingTalk.send_text_msg(content=msg)

    def trade_recode_node(self):
        if len(self.trade_data) == 0:
            return None
        trn1 = copy.copy(self.trade_data[-1])
        merge = False
        if KILINE_PERIOD.index(self.period) < 4:
            merge = True
        if merge and len(self.trade_data) > 1:
            trn2 = copy.copy(self.trade_data[-2])
            trn = TradeRecordNode(trn2.t, trn2.symbol)
            trn.buy = trn1.buy + trn2.buy
            trn.sell = trn1.sell + trn2.sell
            trn.sell_price = trn1.sell_price
            trn.buy_price = trn1.buy_price
            return trn
        return copy.copy(trn1)


record = Record()
