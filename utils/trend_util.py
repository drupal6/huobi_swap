import talib
import numpy as np
from api.model.const import KILINE_PERIOD, CURB_PERIOD


def trend(klines):
    trend = ma_trend(klines)
    if trend > 0:
        return "long"
    elif trend < 0:
        return "short"
    else:
        return None


def ma_trend(klines, symbol):
    w = 0
    for index, period in KILINE_PERIOD:
        df = klines.get("market." + symbol + ".kline." + period)
        df["ma"], df["signal"], df["hist"] = talib.MACD(np.array(df["close"]), fastperiod=12,
                                                        slowperiod=16, signalperiod=9)
        d = 0
        if df["ma"] > df["signal"]:
            d = 1
        else:
            d = -1
        w += CURB_PERIOD * d
    return w


def ichimoku_trend(klines, symbol, period, time_periods=[9, 26, 52]):
    """
    :param klines:
    :param symbol:
    :param period:
    :param time_periods: 【转换线周期,基准线周期,滞后周期】
    :return:
    """
    df = klines.get("market." + symbol + ".kline." + period)
    df["conversion_min"] = talib.MIN(df["low"], time_periods[0])
    df["conversion_max"] = talib.MAX(df["high"], time_periods[0])
    df["conversion"] = (df["conversion_min"] + df["conversion_max"]) / 2
    df["base_min"] = talib.MIN(df["low"], time_periods[1])
    df["base_max"] = talib.MAX(df["high"], time_periods[1])
    df["base"] = (df["base_min"] + df["base_max"]) / 2
    df["leada"] = (df["conversion"] + df["base"]) / 2
    df["leadb_min"] = talib.MIN(df["low"], time_periods[2])
    df["leadb_max"] = talib.MAX(df["high"], time_periods[2])
    df["leadb"] = (df["leadb_min"] + df["leadb_max"]) / 2
    df = df[['id', 'open', 'high', 'low', 'close', 'amount', 'conversion', 'base', 'leada', 'leadb']]
    return 0


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

