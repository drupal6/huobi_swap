from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
import pandas as pd
import mplfinance as mpf
import matplotlib as mpl
from cycler import cycler
from matplotlib import pyplot as plt
import talib
# 图形参数控制
import pylab as pl
import numpy as np
from datetime import datetime
from utils import trend_util
mpl.use('TkAgg')
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
# pd.set_option('precision', 6)  # 浮点数的精度】
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class MatPlot:

    @classmethod
    async def get_data(cls, symbol, period="5min", size=200):
        conversion_periods = 9  # 转换线周期
        base_periods = 26  # 基准线周期
        lagging_span2_periods = 52
        success, error = await request.get_klines(contract_type=symbol, period=period, size=size)
        if error:
            return None
        if success:
            data = success.get("data")
            df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                       'high': 6, 'amount': 7})

            df["conversion_min"] = talib.MIN(df["low"], conversion_periods)
            df["conversion_max"] = talib.MAX(df["high"], conversion_periods)
            df["conversion"] = (df["conversion_min"] + df["conversion_max"]) / 2
            df["base_min"] = talib.MIN(df["low"], base_periods)
            df["base_max"] = talib.MAX(df["high"], base_periods)
            df["base"] = (df["base_min"] + df["base_max"]) / 2
            df["leada"] = (df["conversion"] + df["base"]) / 2
            df["leadb_min"] = talib.MIN(df["low"], lagging_span2_periods)
            df["leadb_max"] = talib.MAX(df["high"], lagging_span2_periods)
            df["leadb"] = (df["leadb_min"] + df["leadb_max"]) / 2
            df["delay_price"] = pd.Series(trend_util.move(df["close"].values.tolist(), -base_periods))
            curr_bar = df.iloc[-1]
            id_values = []
            indexs = []
            for i in range(1, base_periods + 1):
                indexs.append(size - 1 + i)
                id_values.append(int(curr_bar["id"] + i * 5 * 60))
            ids = {"id": pd.Series(id_values, index=indexs)}
            df1 = pd.DataFrame(ids, columns=['id', 'open', 'high', 'low', 'close', 'vol', 'amount'])
            df = df.append(df1, sort=False)
            df["leada"] = pd.Series(trend_util.move(df["leada"].values.tolist(), base_periods))
            df["leadb"] = pd.Series(trend_util.move(df["leadb"].values.tolist(), base_periods))
            df = df[['id', 'open', 'high', 'low', 'close', 'vol', 'amount', 'delay_price', 'conversion', 'base', 'leada', 'leadb']]
            df = df.rename(columns={"id": "date"})
            df["date"] = pd.to_datetime(df["date"], unit="s")
            df.set_index(["date"], inplace=True)
            MatPlot.show(df)

    @classmethod
    def show(cls, df):
        """
        :param symbol:
        :param period:
        :param size:
        :return:
        """

        scale = 100
        delay_price = df["delay_price"]
        conversion = df["conversion"]
        base = df["base"]
        leada = df["leada"]
        leadb = df["leadb"]
        close = df["close"]

        # 设置画布，纵向排列的三个子图
        fig, ax = plt.subplots(1, 1)

        # 设置标签显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 调整子图的间距，hspace表示高(height)方向的间距
        # 设置第一子图的y轴信息及标题
        ax.set_ylabel('Close price in ￥')
        ax.set_title('A_Stock %s ichimoku Indicator' % ("test"))
        delay_price.plot(ax=ax, color='g', lw=1., legend=True, use_index=False)
        conversion.plot(ax=ax, color='r', lw=1., legend=True, use_index=False)
        base.plot(ax=ax, color='b', lw=1., legend=True, use_index=False)
        leada.plot(ax=ax, color='y', lw=1., legend=True, use_index=False)
        leadb.plot(ax=ax, color='k', lw=1., legend=True, use_index=False)
        close.plot(ax=ax, color='c', lw=1., legend=True, use_index=False)

        # 设置间隔，以便图形横坐标可以正常显示（否则数据多了x轴会重叠）
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
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BTC-USD"
    p = "5min"
    c = 300
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MatPlot.get_data(s, p, c))
    loop.close()