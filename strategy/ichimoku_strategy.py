import talib
from strategy.base_strategy import BaseStrategy
import copy
from utils import logger
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
        self.conversion_periods = 9  # 转换线周期
        self.base_periods = 26  # 基准线周期
        self.lagging_span2_periods = 52
        super(IchimokuStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        df = klines.get("market."+self.mark_symbol+".kline." + self.period)
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
        charge_price_dir, cur_price_dir = self.price_ichimoku(last_bar, curr_bar, last_lead, curr_lead)
        change_cb_dir, cur_cb_dir = self.cb_base_ichimoku(last_bar, curr_bar, curr_lead)
        change_delay_dir, cur_delay_dir = self.delay_ichimoku(last_bar, curr_bar, last_delay_lead, curr_delay_lead)
        log = {
            "charge_price_dir": charge_price_dir,
            "cur_price_dir": cur_price_dir,
            "change_cb_dir": change_cb_dir,
            "cur_cb_dir": cur_cb_dir,
            "change_delay_dir": change_delay_dir,
            "cur_delay_dir": cur_delay_dir,
            "close": curr_bar["close"]
        }
        logger.info("IchimokuStrategy", log)

    def price_ichimoku(self, last_bar, curr_bar, last_lead, curr_lead):
        """
        价格与云层
        :return:
        """
        last_min_lead, last_max_lead = self.min_max(last_lead, "leada", "leadb")
        min_lead, max_lead = self.min_max(curr_lead, "leada", "leadb")
        last_close = last_bar["close"]
        close = curr_bar["close"]
        charge_dir = 0
        cur_dir = 0

        if last_close > last_min_lead and close < min_lead:
            charge_dir = -1
        elif last_close < last_max_lead and close > max_lead:
            charge_dir = 1

        if close > max_lead:
            cur_dir = 1
        elif close < min_lead:
            cur_dir = -1
        return charge_dir, cur_dir

    def cb_base_ichimoku(self, last_bar, curr_bar, curr_lead):
        """
        转换线基准线与云层
        :return:
        """
        min_lead, max_lead = self.min_max(curr_lead, "leada", "leadb")
        last_conversion = last_bar["conversion"]
        conversion = curr_bar["conversion"]
        last_base = last_bar["base"]
        base = curr_bar["base"]
        charge_dir = 0
        cur_dir = 0
        if conversion > max_lead and base > max_lead:
            if last_conversion < last_base and conversion > base:
                charge_dir = 1
            if conversion > base:
                cur_dir = 1
        elif conversion < min_lead and base < min_lead:
            if last_conversion > last_base and conversion < base:
                charge_dir = -1
            if conversion < base:
                cur_dir = -1
        return charge_dir, cur_dir

    def delay_ichimoku(self, last_bar, curr_bar, last_delay_lead, curr_delay_lead):
        """
        延迟线与云层
        :return:
        """
        last_delay_min_lead, last_delay_max_lead = self.min_max(last_delay_lead, "leada", "leadb")
        delay_min_lead, delay_max_lead = self.min_max(curr_delay_lead, "leada", "leadb")
        last_close = last_bar["close"]
        close = curr_bar["close"]
        charge_dir = 0
        cur_dir = 0
        if last_close > last_delay_min_lead and close < delay_min_lead:
            charge_dir = -1
        elif last_close < last_delay_max_lead and close > delay_max_lead:
            charge_dir = 1
        if close > delay_max_lead:
            cur_dir = 1
        elif close < delay_min_lead:
            cur_dir = -1
        return charge_dir, cur_dir

    def min_max(self, bar, field1, field2):
        field_value1 = bar[field1]
        field_value2 = bar[field2]
        if field_value1 <= field_value2:
            return field_value1, field_value2
        else:
            return field_value2, field_value1
