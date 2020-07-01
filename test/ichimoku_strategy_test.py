import copy
from utils import ichimoku_util
import pandas as pd
from utils import fileutil
import json
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.
from test.base_strategy_test import BaseStrategyTest


class IchimokuStrategyTest(BaseStrategyTest):
    """
    一目均衡策略
    """
    def __init__(self):
        super(IchimokuStrategyTest, self).__init__()
        self.all_data = None
        self.data1 = None
        self.last_bar = None
        self.ty = None

    def init_log(self):
        pd_data = []
        pd_data1 = []
        lines = fileutil.load_file("../../logs/eth-config.out")
        columns_title = {"Date": 0, 'close': 1, 'cur_price_dir': 2, 'charge_price_dir': 3, 'price_base': 4,
                         'cur_cb_dir': 5, 'change_cb_dir': 6, 'cb_dir': 7, 'cb_change_dir': 8, 'cur_delay_dir': 9,
                         'change_delay_dir': 10, 'zero': 11}
        for line in lines:
            if "IchimokuStrategy:" in line:
                strs = line.split("IchimokuStrategy:")
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
                    "cb_change_dir": data["cb_change_dir"],
                    "cur_delay_dir": data["cur_delay_dir"],
                    "change_delay_dir": data["change_delay_dir"],
                    "zero": 0
                }
                if len(pd_data1) < 2:
                    pd_data1.append(append_data)
                else:
                    pd_data.append(append_data)
        df1 = pd.DataFrame(pd_data1, columns=columns_title)
        self.data1 = df1
        df = pd.DataFrame(pd_data, columns=columns_title)
        self.all_data = df

    def update_data(self, data):
        new_kline = [{
            "Date": data["Date"],
            "close": data["close"],
            "cur_price_dir": data["cur_price_dir"],
            "charge_price_dir": data["charge_price_dir"],
            "price_base": data["price_base"],
            "cur_cb_dir": data["cur_cb_dir"],
            "change_cb_dir": data["change_cb_dir"],
            "cb_dir": data["cb_dir"],
            "cb_change_dir": data["cb_change_dir"],
            "cur_delay_dir": data["cur_delay_dir"],
            "change_delay_dir": data["change_delay_dir"],
            "zero": 0
        }]
        self.data1 = self.data1.append(new_kline, ignore_index=True)

    def strategy_handle(self):
        position = copy.copy(self.position)
        curr_bar = self.data1.iloc[-1]
        self.last_price = curr_bar["close"]
        cur_price_dir = curr_bar["cur_price_dir"]
        charge_price_dir = curr_bar["charge_price_dir"]
        price_base = curr_bar["price_base"]
        cur_cb_dir = curr_bar["cur_cb_dir"]
        change_cb_dir = curr_bar["change_cb_dir"]
        cb_dir = curr_bar["cb_dir"]
        cb_change_dir = curr_bar["cb_change_dir"]
        cur_delay_dir = curr_bar["cur_delay_dir"]
        change_delay_dir = curr_bar["change_delay_dir"]
        open_ret = self.open_position(cur_price_dir, charge_price_dir, cur_cb_dir, change_cb_dir, cb_dir, cb_change_dir,
                                      cur_delay_dir, change_delay_dir)
        close_ret = self.close_position(position, cur_price_dir, price_base, cb_dir, cur_delay_dir)
        self.ty = None
        self.msg = None
        if open_ret:
            if self.long_status == 1:
                self.ty = "多"
            if self.short_status == 1:
                self.ty = "空"
        if close_ret:
            if self.long_status == -1:
                self.ty = "平多"
            if self.short_status == -1:
                self.ty = "平空"
        if self.ty:
            self.msg = "%s [%s] close:%s c_p_d:%s ch_p_d:%s p_b:%s c_c_d:%s ch_c_d:%s c_d:%s c_ch_d:%s c_d_d:%s ch_d_d:%s" % \
                  (self.ty, curr_bar["Date"], curr_bar["close"], curr_bar["cur_price_dir"], curr_bar["charge_price_dir"],
                   curr_bar["price_base"], curr_bar["cur_cb_dir"], curr_bar["change_cb_dir"], curr_bar["cb_dir"],
                   curr_bar["cb_change_dir"], curr_bar["cur_delay_dir"], curr_bar["change_delay_dir"])

    def after_strategy(self):
        super(IchimokuStrategyTest, self).after_strategy()
        if self.deal:
            print(self.msg)
            print("")

    def open_position(self, cur_price_dir, charge_price_dir, cur_cb_dir, change_cb_dir, cb_dir, cb_change_dir,
                      cur_delay_dir, change_delay_dir):
        """
           开仓
           :param cb_change_dir:
           :param cur_price_dir:
           :param charge_price_dir:
           :param cur_cb_dir:
           :param change_cb_dir:
           :param cb_dir:
           :param cur_delay_dir:
           :param change_delay_dir:
           :return:
       """
        if -2 < cur_price_dir + cur_cb_dir + cur_delay_dir < 2 or cur_cb_dir == 0:
            return
        open_long = False
        open_short = False
        # 开多
        if cur_price_dir + cur_cb_dir + cur_delay_dir >= 2 and cb_dir == 1:
            # 价格 云层
            if cur_price_dir == 1 and charge_price_dir == 1:
                open_long = True
                # print("long 价格 云层")
            # 转换线 基准线 云层
            if cur_cb_dir == 1:
                if change_cb_dir == 1 or cb_change_dir == 1:
                    open_long = True
                    # print("long 转换线 基准线 云层")
            # 延迟线 云层
            if cur_delay_dir == 1 and change_delay_dir == 1:
                open_long = True
                # print("long 延迟线 云层")

        if cur_price_dir + cur_cb_dir + cur_delay_dir <= -2 and cb_dir == -1:
            # 价格 云层
            if cur_price_dir == -1 and charge_price_dir == -1:
                open_short = True
                # print("short 价格 云层")
            # 转换线 基准线 云层
            if cur_cb_dir == -1:
                if change_cb_dir == -1 or cb_change_dir == -1:
                    open_short = True
                    # print("short 转换线 基准线 云层")
            # 延迟线 云层
            if cur_delay_dir == -1 and change_delay_dir == -1:
                open_short = True
                # print("short 延迟线 云层")
        if open_long:
            self.long_status = 1
            self.long_trade_size = self.min_volume
            return True
        if open_short:
            self.short_status = 1
            self.short_trade_size = self.min_volume
            return True
        return False

    def close_position(self, position, cur_price_dir, price_base, cb_dir, cur_delay_dir):
        """
              平仓
              :param position:
              :param cur_price_dir:
              :param price_base:
              :param cb_dir:
              :param cur_delay_dir:
              :return:
        """
        close_long = False
        close_short = False
        if position.long_quantity > 0:
            # 转换线基准线反穿
            if cb_dir == -1:
                close_long = True
            # # 价格反穿慢线
            # if price_base == -1:
            #     close_long = True
            # # 延迟线反穿云层
            # if cur_delay_dir == -1:
            #     close_long = True
            # # 价格反穿云层
            # if cur_price_dir == -1:
            #     close_long = True
        if position.short_quantity > 0:
            # 转换线基准线反穿
            if cb_dir == 1:
                close_short = True
            # # 价格反穿慢线
            # if price_base == 1:
            #     close_long = True
            # # 延迟线反穿云层
            # if cur_delay_dir == -1:
            #     close_long = True
            # # 价格反穿云层
            # if cur_price_dir == -1:
            #     close_long = True
        if close_long:
            self.long_status = -1
            return True
        if close_short:
            self.short_status = -1
            return True
        return False


if __name__ == "__main__":
    ist = IchimokuStrategyTest()
    ist.init_log()
    for i in range(0, len(ist.all_data)):
        c_bar = ist.all_data.iloc[i]
        ist.update_data(c_bar)
        ist.on_ticker()
