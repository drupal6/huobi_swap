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
pd.set_option('display.float_format', lambda x:'%.8f' % x)  # 设置不用科学计数法，保留两位小数.


class MatPlot:
    """https://blog.csdn.net/weixin_40014576/article/details/79918819"""
    @classmethod
    def get_data(cls):
        pd_data = []
        lines = fileutil.load_file("../../logs/btc-config.out")
        columns_title = {"Date": 0, 'close': 1, 'cur_price_dir': 2, 'charge_price_dir': 3, 'price_base': 4,
                         'cur_cb_dir': 5, 'change_cb_dir': 6, 'cb_dir': 7, 'cur_delay_dir': 8, 'change_delay_dir': 9,
                         'zero': 10}
        for line in lines:
            if "IchimokuStrategy" in line:
                strs = line.split("IchimokuStrategy")
                date_str = strs[0].split("I [")[1].split(",")[0].rstrip().lstrip()
                json_str = strs[1].rstrip().lstrip().replace("'", "\"")
                data = json.loads(json_str)
                append_data = {
                    "Date": date_str,
                    "close": data["close"],
                    "cur_price_dir": data["cur_price_dir"],
                    "charge_price_dir": data["charge_price_dir"],
                    "price_base": data["price_base"],
                    "cur_cb_dir": data["cur_cb_dir"],
                    "change_cb_dir": data["change_cb_dir"],
                    "cb_dir": data["cb_dir"],
                    "cur_delay_dir": data["cur_delay_dir"],
                    "change_delay_dir": data["change_delay_dir"],
                    "zero": 0
                }
                pd_data.append(append_data)
        df = pd.DataFrame(pd_data, columns=columns_title)
        df.set_index(["Date"], inplace=True)
        MatPlot.show(df)

    @classmethod
    def show(cls, df):
        close_values = df["close"]
        cur_price_dir_values = df["cur_price_dir"]
        charge_price_dir_values = df["charge_price_dir"]
        price_base_values = df["price_base"]
        cur_cb_dir_values = df["cur_cb_dir"]
        change_cb_dir_values = df["change_cb_dir"]
        cb_dir_values = df["cb_dir"]
        cur_delay_dir_values = df["cur_delay_dir"]
        change_delay_dir_values = df["change_delay_dir"]
        zero_values = df["zero"]

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
        close_values.plot(ax=ax[0], color='g', lw=1., legend=True, use_index=False)

        # 应用同步缩放
        ax[1] = plt.subplot(412, sharex=ax[0])
        cur_price_dir_values.plot(ax=ax[1], color='y', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[1], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)

        ax[2] = plt.subplot(413, sharex=ax[0])
        cur_cb_dir_values.plot(ax=ax[2], color='y', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[2], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)

        ax[3] = plt.subplot(414, sharex=ax[0])
        cur_delay_dir_values.plot(ax=ax[3], color='y', lw=1., legend=True, sharex=ax[0], use_index=False)
        zero_values.plot(ax=ax[3], color='r', lw=1., legend=True, sharex=ax[0], use_index=False)

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
