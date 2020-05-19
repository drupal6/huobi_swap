from utils import tools
from utils.dingding import DingTalk


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
        t = tools.get_cur_datetime_m(fmt='%Y-%m-%d %H:%M:%S')
        symbol = self.symbol
        buy = "%.8f" % self.buy
        buy_price = "%.8f" % self.buy_price
        sell = "%.8f" % self.sell
        sell_price = "%.8f" % self.sell_price
        return "%s\nsymbol:%s\nbuy:%s\nsell:%s\nbuy price:%s\nsell price:%s" % (t, symbol, buy, sell, buy_price, sell_price)


class Record:

    def __init__(self):
        self.trade_data = {}
        self.last_notice_time = 0

    def record_trade(self, symbol, tick):
        direction = tick.get("direction")
        quantity = tick.get("amount")
        price = tick.get("price")
        ts = int(tick.get("ts")/1000)
        t = tools.ts_to_datetime_str(ts=ts, fmt="%Y-%m-%d")
        trade_list = self.trade_data.get(symbol)
        if not trade_list:
            trade_list = list()
            self.trade_data[symbol] = trade_list
        trn = None
        if len(trade_list) == 0:
            trn = TradeRecordNode(t, symbol)
            trade_list.append(trn)
        else:
            trn = trade_list[-1]
        if trn.t != t:
            trn = TradeRecordNode(t, symbol)
            trade_list.append(trn)
        trn.add(direction, quantity, price)

    def notice(self):
        notice = True
        if self.last_notice_time > 0:
            ut_time = tools.get_cur_timestamp_ms()
            if self.last_notice_time + 10 * 60 * 1000 > ut_time:
                notice = False
        if not notice:
            return
        self.last_notice_time = tools.get_cur_timestamp_ms()
        msg = ""
        for k, v in self.trade_data.items():
            msg = msg + "\n"
            if len(v) > 0:
                trn = v[-1]
                msg = msg + trn.__str__()
            else:
                msg += k + " not trade data."
        DingTalk.send_text_msg(content=msg)


record = Record()
