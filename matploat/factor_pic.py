import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import talib
# 图形参数控制
import pylab as pl
import numpy as np
from utils import fileutil
from datetime import datetime
mpl.use('TkAgg')
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
# pd.set_option('precision', 6)  # 浮点数的精度】
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class MatPlot:

    @classmethod
    def get_data(cls):
        data = []
        lines = fileutil.load_file("../../logs/btc-config.out")
        for line in lines:
            if "trend:" in line and line.startswith("I"):
                strs = line.rstrip().split(" ")
                t = strs[1][1:] + " " + strs[2][0:8]
                trend = float(strs[5][6:])
                price = float(strs[6][6:])
                other = float(strs[7][6:])
                buy = float(strs[8][4:])
                sell = float(strs[9][5:])
                diff = float(strs[10][5:])
                hist = float(strs[11][5:])
                data.append({"Date": t, "trend": trend, "price": price, "other": other, "buy": buy, "sell": sell, "diff": diff, "hist": hist})
        df = pd.DataFrame(data, columns={"Date": 0, 'trend': 1, 'price': 2, 'other': 3, 'buy': 4, 'sell': 5, 'diff': 6, 'hist': 7})
        df["zero"] = 0
        df.set_index(["Date"], inplace=True)
        MatPlot.show(df)



    @classmethod
    def show(cls, df):
        scale = 100
        price_values = df["price"]
        trend_values = df["trend"]
        diff_values = df["diff"]
        buy_values = df["buy"]
        sell_values = df["sell"]
        zero_values = df["zero"]
        hist_values = df["hist"]

        # 设置画布，纵向排列的三个子图
        fig, ax = plt.subplots(4, 1)

        # 设置标签显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)

        # 设置第一子图的y轴信息及标题
        ax[0].set_ylabel('Close price in ￥')
        ax[0].set_title('A_Stock %s MACD Indicator' % ("test"))
        price_values.plot(ax=ax[0], color='g', lw=1., legend=True, use_index=False)

        # 应用同步缩放
        ax[1] = plt.subplot(412, sharex=ax[0])
        trend_values.plot(ax=ax[1], color='k', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[1], color='g', lw=1., legend=True, sharex=ax[0], use_index=False)

        ax[2] = plt.subplot(413, sharex=ax[0])
        diff_values.plot(ax=ax[2], color='k', lw=1., legend=True, sharex=ax[0], use_index=False)
        buy_values.plot(ax=ax[2], color='b', lw=1., legend=True, sharex=ax[0], use_index=False)
        sell_values.plot(ax=ax[2], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[2], color='g', lw=1., legend=True, sharex=ax[0], use_index=False)

        ax[3] = plt.subplot(414, sharex=ax[0])
        hist_values.plot(ax=ax[3], color='r', kind='bar', legend=True, sharex=ax[0])

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
    MatPlot.get_data()
