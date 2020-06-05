import talib
import numpy as np


def trend(klines):
    trend = ma_trend(klines) + ichimoku_trend(klines) + trade_trend()
    return 0


def ma_trend(klines, symbol, period, macd_periods=[12, 26, 9]):
    """
    1.DIF、DEA均为正，DIF向上突破DEA，买入信号参考。
    2.DIF、DEA均为负，DIF向下跌破DEA，卖出信号参考。
    3.DIF线与K线发生背离，行情可能出现反转信号。
    4.DIF、DEA的值从正数变成负数，或者从负数变成正数并不是交易信号，因为它们落后于市场。
    :param klines:
    :param symbol:
    :param period:
    :param ema_periods:
    :param macd_periods:
    :return:
    """
    df = klines.get("market." + symbol + ".kline." + period)
    if df:
        df['macd'], df['signal'], df['hist'] = talib.MACD(df["close"], fastperiod=macd_periods[0],
                                                                  slowperiod=macd_periods[1], signalperiod=macd_periods[2])
    current_bar = df.iloc[-1]  # 最新的K线 Bar.
    last_bar = df.iloc[-2]
    if current_bar["macd"] > 0 and current_bar["signal"] > 0:
        if current_bar["macd"] > current_bar["signal"] and last_bar["macd"] <= last_bar["macd"]:
            return 1
    if current_bar["macd"] < 0 and current_bar["signal"] < 0:
        if current_bar["macd"] < current_bar["signal"] and last_bar["macd"] >= last_bar["macd"]:
            return -1

    return 0


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

