import pandas as pd
from utils import fileutil
import json
from api.model.const import KILINE_PERIOD
import matplotlib as mpl
from matplotlib import pyplot as plt
# 图形参数控制
import pylab as pl
from datetime import datetime
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
    def get_data(cls, profit, profit_period, size=500):
        pd_data = []
        lines = fileutil.load_file("../../logs/eth-config.out")
        columns_title = {"Date": 0}
        for line in lines:
            if "[data]" in line:
                strs = line.split("[data]")
                date_str = strs[0].split("I [")[1].split(",")[0].rstrip().lstrip()
                json_str = strs[1].rstrip().lstrip().replace("'", "\"")
                data = json.loads(json_str)
                append_data = {"Date": date_str}
                add_columns = len(columns_title) == 1
                close = None
                high = None
                low = None
                for period in KILINE_PERIOD:
                    peroid_json = data[period]
                    append_data[period + "_ma"] = peroid_json["ma"]
                    append_data[period + "_signal"] = peroid_json["signal"]
                    append_data[period + "_hist"] = peroid_json["hist"]
                    append_data[period + "_amount"] = peroid_json["amount"]
                    if close is None:
                        close = float(peroid_json["close"])
                        high = float(peroid_json["high"])
                        low = float(peroid_json["low"])
                    if add_columns:
                        columns_title[period + "_ma"] = len(columns_title)
                        columns_title[period + "_signal"] = len(columns_title)
                        columns_title[period + "_hist"] = len(columns_title)
                        columns_title[period + "_amount"] = len(columns_title)
                append_data["close"] = close
                append_data["high"] = high
                append_data["low"] = low
                columns_title["close"] = len(columns_title)
                columns_title["high"] = len(columns_title)
                columns_title["low"] = len(columns_title)
                pd_data.append(append_data)
        df = pd.DataFrame(pd_data, columns=columns_title)
        df.set_index(["Date"], inplace=True)
        print(df)
        cls.handle_data(df, profit, profit_period, size)

    @classmethod
    def handle_data(cls, df, profit, profit_period, size):
        points = []
        for i in range(1, size - 1):
            if df.iloc[i - 1]["close"] < df.iloc[i]["close"] and df.iloc[i]["close"] >= df.iloc[i + 1]["close"]:
                points.append(NodePoint(i, df.iloc[i]["close"], 1))
            if df.iloc[i - 1]["close"] > df.iloc[i]["close"] and df.iloc[i]["close"] <= df.iloc[i + 1]["close"]:
                points.append(NodePoint(i, df.iloc[i]["close"], -1))

        long_new_points = cls.calculate_points(points, profit, profit_period, 1)
        short_new_points = cls.calculate_points(points, profit, profit_period, -1)
        buy_x, buy_y, sell_x, sell_y = cls.get_points(long_new_points)
        cls.show(df, buy_x, buy_y, sell_x, sell_y)

    @classmethod
    def calculate_points(cls, points, profit, profit_period, dir):
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
                    if dir == 1 and p1.d == -1 and (p2.y - tmp_p1.y)/tmp_p1.y >= profit:
                        new_points.append(tmp_p1)
                        new_points.append(p2)
                        add_point = True
                        i = i + j
                        break
                    if dir == -1 and p1.d == 1 and (tmp_p1.y - p2.y)/tmp_p1.y >= profit:
                        new_points.append(tmp_p1)
                        new_points.append(p2)
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
        price_values = df["close"]

        fig, ax = plt.subplots(1, 1)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 调整子图的间距，hspace表示高(height)方向的间距
        plt.subplots_adjust(hspace=.1)
        # 设置第一子图的y轴信息及标题
        ax.set_ylabel('Close price in ￥')
        ax.set_title('A_Stock %s factor Indicator' % ("test"))
        price_values.plot(ax=ax, color='g', lw=1., legend=True, use_index=False)

        plt.scatter(buy_x, buy_y, s=20, color='r', marker='^', alpha=0.5)
        plt.scatter(sell_x, sell_y, s=20, color='b', marker='^', alpha=0.5)

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
    c = 300
    profit = 0.001
    profit_period = 10
    MatPlot.get_data(profit, profit_period, c)
