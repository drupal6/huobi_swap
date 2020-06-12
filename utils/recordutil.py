from utils import tools
from utils.dingding import DingTalk
from api.model.const import TRADE
from collections import deque
from utils.config import config
import copy


class TradeRecordNode:
    def __init__(self, ts, t, symbol):
        self.ts = ts
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

    def dell(self, direction, quantity):
        if direction.lower() == "buy":
            self.buy -= quantity
        elif direction.lower() == "sell":
            self.sell -= quantity

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
        self.init = False
        self.trade_data = deque()
        self.record_node = None
        self.period = None
        self.period_ts = None
        self.last_notice_time = 0
        self.notice_period = 10 * 60 * 1000
        self.dingding = False

    def record_trade(self, symbol, tick, init=False):
        if not self.period:
            self.period = config.markets.get("period")
            self.period_ts = TRADE[self.period]
            if self.period_ts < self.notice_period:
                self.notice_period = TRADE[self.period]

        if not self.init and not init:
            return
        curr_ts = tools.get_cur_timestamp_ms()
        ts = int(tick.get("ts"))
        if ts + self.period_ts < curr_ts:
            return
        t = tools.ts_to_datetime_str(int(ts / TRADE[self.period]) * TRADE[self.period] / 1000)
        if not self.record_node:
            self.record_node = TradeRecordNode(ts, t, symbol)
        direction = tick.get("direction")
        quantity = tick.get("amount")
        price = tick.get("price")
        self.record_node.add(direction, quantity, price)
        self.trade_data.append(tick)

        if self.init and len(self.trade_data) > 0:
            delete = False
            ts = int(self.trade_data[0]["ts"])
            while (ts + self.period_ts) < curr_ts and len(self.trade_data) > 0:
                delete = True
                old_tick = self.trade_data.popleft()
                old_direction = old_tick.get("direction")
                old_quantity = old_tick.get("amount")
                self.record_node.dell(old_direction, old_quantity)
                ts = int(self.trade_data[0]["ts"])
            if delete:
                t = tools.ts_to_datetime_str(int(ts / TRADE[self.period]) * TRADE[self.period] / 1000)
                self.record_node.ts = ts
                self.record_node.t = t
        self.notice()

    def trade_record_node(self):
        if self.record_node:
            return copy.copy(self.record_node)
        return None

    def notice(self):
        if not self.dingding:
            return
        notice = True
        if self.last_notice_time > 0:
            ut_time = tools.get_cur_timestamp_ms()
            if self.last_notice_time + self.notice_period > ut_time:
                notice = False
        if not notice:
            return
        self.last_notice_time = tools.get_cur_timestamp_ms()
        if self.record_node:
            msg = self.record_node.__str__()
            DingTalk.send_text_msg(content=msg)


record = Record()
