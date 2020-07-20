import pandas as pd
from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
import matplotlib as mpl
from matplotlib import pyplot as plt
# 图形参数控制
import pylab as pl
import numpy as np
from sklearn import svm
from datetime import datetime
import talib
from collections import deque
from utils import sigle_linear_regression_util
mpl.use('TkAgg')
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class NodePoint:
    def __init__(self, x, y, d):
        self.x = x
        self.y = y
        self.d = d
        self.l = 0


class MatPlot:

    @classmethod
    async def get_data(cls, profit, profit_period, symbol, period="15min", size=500):
        success, error = await request.get_klines(contract_type=symbol, period=period, size=1000)
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
            df["Leading"] = np.nan
            df["k"] = np.nan
            df["b"] = np.nan
            df["c"] = np.nan
            df["Date"] = pd.to_datetime(df["Date"], unit="s")
            df.set_index(["Date"], inplace=True)

            df_lenght = len(df)
            period_1 = 10
            y_d = deque(maxlen=period_1)
            x_x = np.arange(1, period_1 + 1, 1)
            for i in range(0, df_lenght):
                if len(y_d) == period_1 and i < df_lenght:
                    leading_y, k, b = sigle_linear_regression_util.leading_y(x_x, y_d)
                    df.iloc[i, 5] = leading_y
                    df.iloc[i, 6] = k
                    df.iloc[i, 7] = b
                y_d.append(df.iloc[i]["Close"])

            cls.handle_data(df, profit, profit_period, period_1, size)

    @classmethod
    def handle_data(cls, df, profit, profit_period, period_1, size):
        points = []
        for i in range(1, size - 1):
            if df.iloc[i - 1]["Close"] < df.iloc[i]["Close"] and df.iloc[i]["Close"] >= df.iloc[i + 1]["Close"]:
                points.append(NodePoint(i, df.iloc[i]["Close"], 1))
            if df.iloc[i - 1]["Close"] > df.iloc[i]["Close"] and df.iloc[i]["Close"] <= df.iloc[i + 1]["Close"]:
                points.append(NodePoint(i, df.iloc[i]["Close"], -1))

        long_new_points = cls.calculate_points(df, points, profit, profit_period, 1)
        short_new_points = cls.calculate_points(df, points, profit, profit_period, -1)
        svm_model = cls.svn_train(df, period_1, long_new_points, size)
        cls.svn_predict(svm_model, df, long_new_points, size)
        buy_x, buy_y, sell_x, sell_y = cls.get_points(long_new_points)
        cls.show(df, buy_x, buy_y, sell_x, sell_y)

    @classmethod
    def svn_train(cls, df, period_1, long_new_points, size):
        x_train = []  # 特征
        y_train = []  # 标记

        p_index = 0
        p1 = long_new_points[p_index]
        p2 = long_new_points[p_index + 1]
        count = 0
        for i in range(period_1, size):
            features = []
            cur_bar = df.iloc[i]
            close = float(cur_bar["k"])
            leading = float(cur_bar["b"])
            features.append(close - leading)

            if i > p2.x and p_index + 2 < len(long_new_points):
                p_index = p_index + 2
                p1 = long_new_points[p_index]
                p2 = long_new_points[p_index + 1]
            if p_index + 2 > len(long_new_points):
                break

            label = False
            if p1.x == i or p2.x == i:
                label = True
                count = count + 1
            x_train.append(features)
            y_train.append(label)
        svm_module = svm.SVC()
        svm_module.fit(x_train, y_train)
        return svm_module

    @classmethod
    def svn_predict(cls, svm_module, df, long_new_points, size):
        last_flag = None
        for i in range(size, len(df)):
            x = []  # 特征
            features = []
            cur_bar = df.iloc[i]
            close = float(cur_bar["k"])
            leading = float(cur_bar["b"])
            features.append(close - leading)
            x.append(features)
            flag = svm_module.predict(x)
            if bool(flag):
                if last_flag is None:
                    last_flag = True
                else:
                    if last_flag is False and long_new_points[-1].d == -1:
                        long_new_points.append(NodePoint(i, cur_bar["Close"], 1))
                    last_flag = True
            elif bool(flag) is False:
                if last_flag is None:
                    last_flag = False
                else:
                    if last_flag is True and long_new_points[-1].d == 1:
                        long_new_points.append(NodePoint(i, cur_bar["Close"], -1))
                    last_flag = False
            else:
                last_flag = None

    @classmethod
    def calculate_points(cls, df, points, profit, profit_period, dir):
        new_points = []
        i = 0
        l = len(points)
        while i < l:
            p1 = points[i]
            add_point = False
            tmp_p1 = p1
            for j in range(1, profit_period):
                if i + j > l - 1:
                    break
                p2 = points[i + j]
                if p1.d == p2.d:
                    if dir == 1 and p1.d == -1 and p1.y > p2.y:
                        tmp_p1 = p2
                    if dir == -1 and p1.d == 1 and p1.y < p2.y:
                        tmp_p1 = p2
                else:
                    if dir == 1 and p1.d == -1 and (p2.y - tmp_p1.y) / tmp_p1.y >= profit:
                        new_points.append(tmp_p1)
                        new_points.append(p2)
                        print(df.iloc[tmp_p1.x].k, df.iloc[tmp_p1.x].b, df.iloc[p2.x].k, df.iloc[p2.x].b, 1)
                        add_point = True
                        i = i + j
                        break
                    if dir == -1 and p1.d == 1 and (tmp_p1.y - p2.y) / tmp_p1.y >= profit:
                        new_points.append(tmp_p1)
                        new_points.append(p2)
                        print(df.iloc[tmp_p1.x].k, df.iloc[tmp_p1.x].b, df.iloc[p2.x].k, df.iloc[p2.x].b, -1)
                        add_point = True
                        i = i + j
                        break

            if not add_point:
                i = i + 1
        return new_points

    @classmethod
    def get_points(cls, points):
        buy_x = []
        buy_y = []
        sell_x = []
        sell_y = []
        for i in range(0, len(points)):
            p = points[i]
            if p.d == 1:
                sell_x.append(p.x)
                sell_y.append(p.y)
            if p.d == -1:
                buy_x.append(p.x)
                buy_y.append(p.y)
        return buy_x, buy_y, sell_x, sell_y

    @classmethod
    def show(cls, df, buy_x, buy_y, sell_x, sell_y):
        price_values = df["Close"]
        leading_values = df["Leading"]
        high_values = df["High"]
        low_values = df["Low"]

        fig, ax = plt.subplots(1, 1)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)
        # 设置第一子图的y轴信息及标题
        ax.set_ylabel('Close price in ￥')
        ax.set_title('A_Stock %s factor Indicator' % ("test"))
        price_values.plot(ax=ax, color='g', lw=1., legend=True, use_index=False)
        leading_values.plot(ax=ax, color='r', lw=1., legend=True, use_index=False)
        # high_values.plot(ax=ax, color='y', lw=1., legend=True, use_index=False)
        # low_values.plot(ax=ax, color='y', lw=1., legend=True, use_index=False)

        plt.scatter(buy_x, buy_y, s=50, color='r', marker='^', alpha=0.5)
        plt.scatter(sell_x, sell_y, s=50, color='b', marker='^', alpha=0.5)

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
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BTC-USD"
    p = "15min"
    c = 300
    profit = 0.001
    profit_period = 10
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MatPlot.get_data(profit, profit_period, s, p, c))
    loop.close()
