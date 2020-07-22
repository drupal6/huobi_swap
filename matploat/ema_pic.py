import pandas as pd
from api.huobi.huobi_request import HuobiRequest
import asyncio
import matplotlib as mpl
from matplotlib import pyplot as plt
# 图形参数控制
import pylab as pl
import numpy as np
from utils import fileutil
from datetime import datetime
import talib
from collections import deque
from utils import sigle_linear_regression_util
mpl.use('TkAgg')
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class MatPlot:

    @classmethod
    async def get_data(cls, symbol, period="15min", size=500):
        success, error = await request.get_klines(contract_type=symbol, period=period, size=size)
        if error:
            print(error)
            return None
        if success:
            data = success.get("data")
            df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                             'high': 6, 'amount': 7})
            df = df[['id', 'open', 'high', 'low', 'close', 'vol']]
            df = df.rename(
                columns={"id": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "vol": "Volume"})
            df["Date"] = pd.to_datetime(df["Date"], unit="s")
            df.set_index(["Date"], inplace=True)
            MatPlot.show(df)

    @classmethod
    def show(cls, df):
        df['fast_ema'] = talib.EMA(df['Close'], timeperiod=5)
        df['slow_ema'] = talib.EMA(df['Close'], timeperiod=10)
        price_values = df["Close"]
        fast_ema_values = df['fast_ema']
        slow_ema_values = df['slow_ema']

        # 设置画布，纵向排列的三个子图
        fig, ax = plt.subplots(1, 1)
        # 设置标签显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)
        # 设置第一子图的y轴信息及标题
        ax.set_ylabel('Close price in ￥')
        ax.set_title('A_Stock %s MACD Indicator' % ("test"))

        price_values.plot(ax=ax, color='g', lw=1., legend=True, use_index=False)
        fast_ema_values.plot(ax=ax, color='r', lw=1., legend=True, use_index=False)
        slow_ema_values.plot(ax=ax, color='b', lw=1., legend=True, use_index=False)

        # plt.scatter([100], [9300], s=100, color='y',marker='^', alpha=0.5)

        # 设置间隔，以便图形横坐标可以正常显示（否则数据多了x轴会重叠）
        scale = 100
        interval = scale // 20
        # 设置x轴参数，应用间隔设置
        # 时间序列转换，(否则日期默认会显示时分秒数据00:00:00)
        # x轴标签旋转便于显示
        pl.xticks([i for i in range(1, scale + 1, interval)],
                  [datetime.strftime(i, format='%Y-%m-%d') for i in
                   pd.date_range(df.index[0], df.index[-1], freq='%dd' % (interval))],
                  rotation=45)
        plt.show()


if __name__ == "__main__":
    request = HuobiRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BSV_CQ"
    p = "60min"
    c = 300
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MatPlot.get_data(s, p, c))
    loop.close()
