from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
import pandas as pd
import talib
import copy
from test.base_strategy_test import BaseStrategyTest
from utils import ichimoku_util


class IchimokuStrategy1Test(BaseStrategyTest):
    def __init__(self, symbol, period="5min", size=2000):
        super(IchimokuStrategy1Test, self).__init__()
        self.symbol = symbol
        self.period = period
        self.size = size
        self._klines_max_size = 500
        self.conversion_periods = 9  # 转换线周期
        self.base_periods = 26  # 基准线周期
        self.lagging_span2_periods = 52
        self.all_data = None
        self.data1 = None
        self.last_bar = None
        self.ty = None

    async def get_data(self):
        success, error = await request.get_klines(contract_type=self.symbol, period=self.period, size=self.size)
        if error:
            return None
        if success:
            data = success.get("data")
            df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5, 'high': 6})
            df = df[['id', 'open', 'high', 'low', 'close', 'vol']]
            self.all_data = df
            self.update_data()

    def update_data(self):
        for i in range(0, len(self.all_data)):
            cur_bar = self.all_data.iloc[i]
            new_kline = [{'id': cur_bar["id"], 'open': cur_bar["open"], 'high': cur_bar["high"], 'low': cur_bar["low"],
                          'close': cur_bar["close"]}]
            if self.data1 is None:
                d = pd.DataFrame(new_kline, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4,
                                                              'low': 5, 'high': 6})
                self.data1 = d[['id', 'open', 'high', 'low', 'close', 'vol']]
            else:
                self.data1 = self.data1.append(new_kline, ignore_index=True)
            if len(self.data1) > self._klines_max_size:
                self.data1.drop(self.data1.index[0], inplace=True)
                self.data1.reset_index(drop=True, inplace=True)
            if len(self.data1) >= self.klines_max_size:
                self.on_ticker()

    def strategy_handle(self):
        position = copy.copy(self.position)
        df = copy.copy(self.data1)
        df["conversion_min"] = talib.MIN(df["low"], self.conversion_periods)
        df["conversion_max"] = talib.MAX(df["high"], self.conversion_periods)
        df["conversion"] = (df["conversion_min"] + df["conversion_max"]) / 2
        df["base_min"] = talib.MIN(df["low"], self.base_periods)
        df["base_max"] = talib.MAX(df["high"], self.base_periods)
        df["base"] = (df["base_min"] + df["base_max"]) / 2
        df["leada"] = (df["conversion"] + df["base"]) / 2
        df["leadb_min"] = talib.MIN(df["low"], self.lagging_span2_periods)
        df["leadb_max"] = talib.MAX(df["high"], self.lagging_span2_periods)
        df["leadb"] = (df["leadb_min"] + df["leadb_max"]) / 2
        df = df[['id', 'open', 'high', 'low', 'close', 'conversion', 'base', 'leada', 'leadb']]
        last_bar = df.iloc[-2]
        curr_bar = df.iloc[-1]
        self.last_price = curr_bar["close"]
        last_lead = df.iloc[-self.base_periods - 1]
        curr_lead = df.iloc[-self.base_periods]
        last_delay_lead = df.iloc[-self.lagging_span2_periods - 1]
        curr_delay_lead = df.iloc[-self.lagging_span2_periods]
        cur_lead_dir, charge_lead_dir = ichimoku_util.lead_dir(last_bar, curr_bar)
        cur_price_dir, charge_price_dir, price_base = ichimoku_util.price_ichimoku(last_bar, curr_bar, last_lead,
                                                                                   curr_lead)
        cur_cb_dir, change_cb_dir, cb_dir, cb_change_dir = ichimoku_util.cb_base_ichimoku(last_bar, curr_bar, last_lead,
                                                                                          curr_lead)
        cur_delay_dir, change_delay_dir = ichimoku_util.delay_ichimoku(last_bar, curr_bar, last_delay_lead,
                                                                       curr_delay_lead)
        log = {
            "cur_lead_dir": cur_lead_dir,
            "charge_lead_dir": charge_lead_dir,
            "cur_price_dir": cur_price_dir,
            "charge_price_dir": charge_price_dir,
            "price_base": price_base,
            "cur_cb_dir": cur_cb_dir,
            "change_cb_dir": change_cb_dir,
            "cb_dir": cb_dir,
            "cb_change_dir": cb_change_dir,
            "cur_delay_dir": cur_delay_dir,
            "change_delay_dir": change_delay_dir,
            "close": curr_bar["close"]
        }
        # print(log)
        self.open_position(cur_price_dir, charge_price_dir, cur_cb_dir, change_cb_dir, cb_dir, cb_change_dir,
                           cur_delay_dir, change_delay_dir)
        self.close_position(position, cur_price_dir, price_base, cb_dir, cur_delay_dir)

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
        if cur_price_dir + cur_cb_dir + cur_delay_dir >= 2:
            # 价格 云层
            if cur_price_dir == 1 and charge_price_dir == 1:
                open_long = True
            # 转换线 基准线 云层
            if cur_cb_dir == 1 and cb_dir == 1:
                if change_cb_dir == 1 or cb_change_dir == 1:
                    open_long = True
            # 延迟线 云层
            if cur_delay_dir == 1 and change_delay_dir == 1:
                open_long = True

        if cur_price_dir + cur_cb_dir + cur_delay_dir <= -2:
            # 价格 云层
            if cur_price_dir == -1 and charge_price_dir == -1:
                open_short = True
            # 转换线 基准线 云层
            if cur_cb_dir == -1 and cb_dir == -1:
                if change_cb_dir == -1 or cb_change_dir == -1:
                    open_short = True
            # 延迟线 云层
            if cur_delay_dir == -1 and change_delay_dir == -1:
                open_short = True
        if open_long:
            self.long_status = 1
            self.long_trade_size = self.min_volume
        if open_short:
            self.short_status = 1
            self.short_trade_size = self.min_volume

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
        if position.long_quantity - self.long_fixed_position > 0:
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
        if position.short_quantity - self.short_fixed_position > 0:
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
        if close_short:
            self.short_status = -1


if __name__ == "__main__":
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BTC-USD"
    p = "5min"
    c = 2000
    ist = IchimokuStrategy1Test(s, p, c)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ist.get_data())
    loop.close()
