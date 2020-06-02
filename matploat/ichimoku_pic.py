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
from datetime import datetime
mpl.use('TkAgg')


class MatPlot:

    @classmethod
    async def get_data(cls, symbol, period="5min", size=200):
        success, error = await request.get_klines(contract_type=symbol, period=period, size=size)
        if error:
            return None
        if success:
            data = success.get("data")
            df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                       'high': 6, 'amount': 7})
            df = df[['id', 'open', 'high', 'low', 'close', 'vol', 'amount']]
            df = df.rename(columns={"id": "date"})
            df["date"] = pd.to_datetime(df["date"], unit="s")
            df.set_index(["date"], inplace=True)
            MatPlot.show(df, symbol, period, size)

    @classmethod
    def show(cls, df, symbol, period="1min", time_periods=[9, 26, 52]):
        """
        :param symbol:
        :param period:
        :param size:
        :return:
        """
        scale = 100
        df["conversion_min"] = talib.MIN(df["low"], 9)
        df["conversion_max"] = talib.MAX(df["high"], 9)
        df["conversion"] = (df["conversion_min"] + df["conversion_max"]) / 2
        df["base_min"] = talib.MIN(df["low"], 26)
        df["base_max"] = talib.MAX(df["high"], 26)
        df["base"] = (df["base_min"] + df["base_max"]) / 2
        df["leada"] = (df["conversion"] + df["base"]) / 2
        df["leadb_min"] = talib.MIN(df["low"], 52)
        df["leadb_max"] = talib.MAX(df["high"], 52)
        df["leadb"] = (df["leadb_min"] + df["leadb_max"]) / 2

        close_price = df["close"]
        conversion = df["conversion"]
        base = df["base"]
        leada = df["leada"]
        leadb = df["leadb"]

        # 设置画布，纵向排列的三个子图
        fig, ax = plt.subplots(2, 1)

        # 设置标签显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)

        # 设置第一子图的y轴信息及标题
        ax[0].set_ylabel('Close price in ￥')
        ax[0].set_title('A_Stock %s MACD Indicator' % ("test"))
        close_price.plot(ax=ax[0], color='g', lw=1., legend=True, use_index=False)
        conversion.plot(ax=ax[0], color='r', lw=1., legend=True, use_index=False)
        base.plot(ax=ax[0], color='b', lw=1., legend=True, use_index=False)
        leada.plot(ax=ax[0], color='y', lw=1., legend=True, use_index=False)
        leadb.plot(ax=ax[0], color='k', lw=1., legend=True, sharex=ax[0], use_index=False)


        # 应用同步缩放
        ax[1] = plt.subplot(212, sharex=ax[0])


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