import talib
from utils import logger
import numpy as np
from api.model.const import KILINE_PERIOD
from utils.recordutil import record


def trend(klines, symbol):
    ma_trend(klines, symbol)
    return "lock"


def ma_trend(klines, symbol):
    trade_record_node = record.trade_record_node()
    if not trade_record_node:
        return
    data = {
        "buy": trade_record_node.buy,
        "sell": trade_record_node.sell
    }
    for index, period in enumerate(KILINE_PERIOD):
        df = klines.get("market." + symbol + ".kline." + period)
        df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12,
                                                        slowperiod=26, signalperiod=9)
        curr_bar = df.iloc[-1]
        ma = curr_bar["ma"]
        signal = curr_bar["signal"]
        hist = curr_bar["hist"]
        close = curr_bar["close"]
        amount = curr_bar["amount"]
        d = {
            "ma": ma,
            "signal": signal,
            "hist": hist,
            "close": close,
            "amount": amount,
        }
        data[period] = d
    logger.info("[data]", data)


def trade_trend():
    return 0


def move(data, offset):
    i = len(data)
    if offset == 0:
        return data
    elif offset < 0:
        return data[-offset:i]
    else:
        new_data = np.zeros(i + offset)
        for j in range(0, offset):
            new_data[j] = np.nan
        new_data[offset:i+offset] = data[0:i]
        return new_data[0:i]

