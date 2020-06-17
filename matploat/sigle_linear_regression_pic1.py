import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
from collections import deque
from utils import sigle_linear_regression_util
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import copy
import talib
# 图形参数控制
import pylab as pl
import numpy as np
from utils import fileutil
from datetime import datetime
from utils import tools
import json
from api.model.const import KILINE_PERIOD
mpl.use('TkAgg')
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
# pd.set_option('precision', 6)  # 浮点数的精度】
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class MatPlot:
    """https://blog.csdn.net/weixin_40014576/article/details/79918819"""
    @classmethod
    def get_data(cls):
        pd_data = []
        lines = fileutil.load_file("../../logs/btc-config4.out")
        columns_title = {"Date": 0, 'zero': 1, 'leading': 2}
        for line in lines:
            if "[data]" in line:
                strs = line.split("[data]")
                date_str = strs[0].split("I [")[1].split(",")[0].rstrip().lstrip()
                json_str = strs[1].rstrip().lstrip().replace("'", "\"")
                data = json.loads(json_str)
                append_data = {"Date": date_str, "zero": 0, "leading": 0}
                add_columns = len(columns_title) == 3
                for period in KILINE_PERIOD:
                    peroid_json = data[period]
                    append_data[period + "_ma"] = peroid_json["ma"]
                    append_data[period + "_signal"] = peroid_json["signal"]
                    append_data[period + "_hist"] = peroid_json["hist"]
                    append_data[period + "_close"] = peroid_json["close"]
                    append_data[period + "_amount"] = peroid_json["amount"]
                    append_data[period + "_buy"] = float(peroid_json["buy"])
                    append_data[period + "_sell"] = float(peroid_json["sell"])
                    append_data[period + "_z"] = float(peroid_json["buy"]) - float(peroid_json["sell"])
                    if add_columns:
                        columns_title[period + "_ma"] = len(columns_title)
                        columns_title[period + "_signal"] = len(columns_title)
                        columns_title[period + "_hist"] = len(columns_title)
                        columns_title[period + "_close"] = len(columns_title)
                        columns_title[period + "_amount"] = len(columns_title)
                        columns_title[period + "_buy"] = len(columns_title)
                        columns_title[period + "_sell"] = len(columns_title)
                        columns_title[period + "_z"] = len(columns_title)
                pd_data.append(append_data)
        df = pd.DataFrame(pd_data, columns=columns_title)
        df.set_index(["Date"], inplace=True)
        MatPlot.show(df)

    @classmethod
    def show(cls, df):
        period = "5min"
        df["hist"] = df["1min_hist"] + df["5min_hist"] + df["15min_hist"] + df["30min_hist"] + df["60min_hist"] \
                     + df["4hour_hist"] + df["1day_hist"]
        df_simple = df[['hist', period + '_close']]
        df_simple = df_simple[0:300]
        print(df_simple)
        print(df_simple.corr())
        X_train, X_test, Y_train, Y_test = train_test_split(df_simple.iloc[:, :1], df_simple[period + "_close"],
                                                            train_size=.90)
        print("原始数据特征:", df_simple.iloc[:, :2].shape,
              ",训练数据特征:", X_train.shape,
              ",测试数据特征:", X_test.shape)

        print("原始数据标签:", df_simple[period + "_close"].shape,
              ",训练数据标签:", Y_train.shape,
              ",测试数据标签:",Y_test.shape)
        X_train = X_train.values.reshape(-1, 1)
        model = LinearRegression()
        model.fit(X_train, Y_train)
        a = model.intercept_
        b = model.coef_
        print(a, b)
        for i in range(0, len(df)):
            cur_bar = df.iloc[i]
            df.iloc[i, 1] = a + b[0] * cur_bar["hist"]
        df["buy_sell"] = df["1min_buy"] - df["1min_sell"]
        df["buy_sell_ma"], df["buy_sell_signal"], df["buy_sell_hist"] = talib.MACD(np.array(df["buy_sell"]), fastperiod=12,
                                                                                   slowperiod=26, signalperiod=9)
        df["1min_hist"] = df["1min_hist"] + df["5min_hist"] + df["15min_hist"] + df["30min_hist"] + df["60min_hist"]
        df["1min_hist"] = talib.SMA(df["1min_hist"], timeperiod=20)
        close_values = df["1min_close"]
        hist_1min_values = df["1min_hist"]
        hist_5min_values = df["5min_hist"]
        hist_15min_values = df["15min_hist"]
        hist_30min_values = df["30min_hist"]
        hist_60min_values = df["60min_hist"]
        hist_4hour_values = df["4hour_hist"]
        hist_1day_values = df["1day_hist"]
        buy_sell_values = df["buy_sell"]
        buy_sell_hist = df["buy_sell_hist"]
        leading_value = df["leading"]
        zero_values = df["zero"]

        # 设置画布，纵向排列的三个子图
        fig, ax = plt.subplots(3, 1)

        # 设置标签显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)

        # 设置第一子图的y轴信息及标题
        ax[0].set_ylabel('Close price in ￥')
        ax[0].set_title('A_Stock %s MACD Indicator' % ("test"))
        close_values.plot(ax=ax[0], color='g', lw=1., legend=True, use_index=False)
        leading_value.plot(ax=ax[0], color='r', lw=1., legend=True, use_index=False)

        # 应用同步缩放
        ax[1] = plt.subplot(312, sharex=ax[0])
        hist_1min_values.plot(ax=ax[1], color='k', lw=1., legend=True, sharex=ax[0], use_index=False)
        hist_5min_values.plot(ax=ax[1], color='y', lw=1., legend=True, sharex=ax[0], use_index=False)
        hist_15min_values.plot(ax=ax[1], color='c', lw=1., legend=True, sharex=ax[0], use_index=False)
        # hist_30min_values.plot(ax=ax[1], color='b', lw=1., legend=True, sharex=ax[0], use_index=False)
        # hist_60min_values.plot(ax=ax[1], color='g', lw=1., legend=True, sharex=ax[0], use_index=False)
        # hist_4hour_values.plot(ax=ax[1], color='m', lw=1., legend=True, sharex=ax[0], use_index=False)
        # hist_1day_values.plot(ax=ax[1], color='c', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[1], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)

        ax[2] = plt.subplot(313, sharex=ax[0])
        buy_sell_values.plot(ax=ax[2], color='k', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[2], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)

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
    MatPlot.get_data()
