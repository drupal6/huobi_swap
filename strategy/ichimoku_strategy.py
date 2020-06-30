import talib
from strategy.base_strategy import BaseStrategy
import copy
from utils import logger, ichimoku_util
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)  # 最多显示行数.
# pd.set_option('precision', 6)  # 浮点数的精度】
pd.set_option('display.float_format', lambda x:'%.2f' % x)  # 设置不用科学计数法，保留两位小数.


class IchimokuStrategy(BaseStrategy):
    """
    一目均衡策略
    """
    def __init__(self):
        self.conversion_periods = 5  # 转换线周期
        self.base_periods = 24  # 基准线周期
        self.lagging_span2_periods = 48
        super(IchimokuStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        position = copy.copy(self.position)
        df = klines.get("market.%s.kline.%s" % (self.mark_symbol, self.period))
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
        df = df[['id', 'open', 'high', 'low', 'close', 'amount', 'conversion', 'base', 'leada', 'leadb']]
        last_bar = df.iloc[-2]
        curr_bar = df.iloc[-1]
        last_lead = df.iloc[-self.base_periods - 1]
        curr_lead = df.iloc[-self.base_periods]
        last_delay_lead = df.iloc[-self.lagging_span2_periods - 1]
        curr_delay_lead = df.iloc[-self.lagging_span2_periods]
        cur_price_dir, charge_price_dir, price_base = ichimoku_util.price_ichimoku(last_bar, curr_bar, last_lead, curr_lead)
        cur_cb_dir, change_cb_dir, cb_dir, cb_change_dir = ichimoku_util.cb_base_ichimoku(last_bar, curr_bar, last_lead, curr_lead)
        cur_delay_dir, change_delay_dir = ichimoku_util.delay_ichimoku(last_bar, curr_bar, last_delay_lead, curr_delay_lead)
        log = {
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
        logger.info("IchimokuStrategy:", log)
        if self.test:
            return
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
        if -2 < cur_price_dir + cur_cb_dir + cur_delay_dir < 2:
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
                close_long = True
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
