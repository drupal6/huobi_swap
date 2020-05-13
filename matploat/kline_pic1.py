from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib as mpl
from cycler import cycler
from matplotlib import pyplot as plt
import talib
mpl.use('TkAgg')


class MatPlot:

    @classmethod
    async def get_data(cls, symbol, period="1min", size=200):
        success, error = await request.get_klines(contract_type=symbol, period=period, size=size)
        if error:
            return None
        if success:
            data = success.get("data")
            df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                       'high': 6, 'amount': 7})
            df = df[['id', 'open', 'high', 'low', 'close', 'vol']]
            df = df.rename(
                columns={"id": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "vol": "Volume"})
            df["Date"] = pd.to_datetime(df["Date"], unit="s")
            df.set_index(["Date"], inplace=True)
            MatPlot.show(df, symbol, period, size)

    @classmethod
    def show(cls, df, symbol, period="1min", size=200):
        df['fast_ema'] = talib.EMA(df['Close'], timeperiod=5)
        df['slow_ema'] = talib.EMA(df['Close'], timeperiod=10)
        x_k = []
        close_k = []
        fast_ema = []
        slow_ema = []
        for i in range(0, len(df)):
            x_k.append(i)
            close_k.append(df.iloc[i]["Close"])
            fast_ema.append(df.iloc[i]["fast_ema"])
            slow_ema.append(df.iloc[i]["slow_ema"])

        plt.plot(x_k, close_k, label="close")
        plt.plot(x_k, fast_ema, label="fast")
        plt.plot(x_k, slow_ema, label="show")
        plt.legend()
        plt.show()


if __name__ == "__main__":
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BTC-USD"
    p = "5min"
    c = 200
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MatPlot.get_data(s, p, c))
    loop.close()
