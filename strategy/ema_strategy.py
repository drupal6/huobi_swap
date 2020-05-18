import talib
from strategy.base_strategy import BaseStrategy
import copy


class EmaStrategy(BaseStrategy):
    """
    移动平均线策略
    """

    def __init__(self):
        super(EmaStrategy, self).__init__()

    def strategy_handle(self):
        klines = copy.copy(self.klines)
        df = klines.get("market."+self.mark_symbol+".kline." + self.period)
        df['fast_ema'] = talib.EMA(df['close'], timeperiod=self.fast_ema_window)
        df['slow_ema'] = talib.EMA(df['close'], timeperiod=self.slow_ema_window)

        current_bar = df.iloc[-1]  # 最新的K线 Bar.
        last_bar = df.iloc[-2]
        if current_bar["fast_ema"] > current_bar["slow_ema"] and last_bar["fast_ema"] <= last_bar["slow_ema"]:
            self.long_status == 1
            self.long_trade_size = self.min_volume
            self.short_status == -1

        if current_bar["fast_ema"] < current_bar["slow_ema"] and last_bar["fast_ema"] >= last_bar["slow_ema"]:
            self.long_status == -1
            self.short_status == 1
            self.short_trade_size = self.min_volume








