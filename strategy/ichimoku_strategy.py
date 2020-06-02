import talib
from utils.tools import round_to
from strategy.base_strategy import BaseStrategy
import copy
from utils import logger


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
        print(df)









