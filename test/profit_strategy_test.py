from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
import pandas as pd
import talib


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
        df['fast_ema'] = talib.EMA(df['Close'], timeperiod=3)
        df['slow_ema'] = talib.EMA(df['Close'], timeperiod=6)
        df = df.dropna(axis=0, how='any')
        df_size = len(df)
        long_size = 0
        long_price = 0
        long_index = 0
        short_size = 0
        short_price = 0
        short_index = 0
        profit = 0
        long_count = 0
        short_count = 0
        long_profit_per = 0.15
        short_profit_per = 0.15
        long_stop_loss_per = -0.5
        short_stop_loss_per = -2
        lever_rate = 50
        fee_rate = 0.002
        for i in range(0, df_size):
            if i == 0:
                continue
            if i == df_size - 1:
                break;
            last_bar = df.iloc[i-1]
            current_bar = df.iloc[i]
            has_long = False
            if long_size > 0 and long_price > 0:
                has_long = True
                # if i - long_index > 10:
                #     temp_profit = (current_bar["Close"] - long_price) * lever_rate / long_price
                #     long_size = 0
                #     long_price = 0
                #     profit += temp_profit
                # else:
                temp_profit = (current_bar["High"] - long_price) * lever_rate / long_price
                if temp_profit >= long_profit_per:
                    long_size = 0
                    long_price = 0
                    profit += temp_profit
                else:
                    temp_profit = (current_bar["Low"] - long_price) * lever_rate / long_price
                    if temp_profit <= long_stop_loss_per:
                        long_size = 0
                        long_price = 0
                        profit += temp_profit

            has_short = False
            if short_size > 0 and short_price > 0:
                has_short = True
                # if i - short_index > 10:
                #     temp_profit = (short_price - current_bar["Close"]) * lever_rate / short_price
                #     short_size = 0
                #     short_price = 0
                #     profit += temp_profit
                # else:
                temp_profit = (short_price - current_bar["Low"]) * lever_rate / short_price
                if temp_profit >= short_profit_per:
                    short_size = 0
                    short_price = 0
                    profit += temp_profit
                else:
                    temp_profit = (short_price - current_bar["High"]) * lever_rate / short_price
                    if temp_profit <= short_stop_loss_per:
                        short_size = 0
                        short_price = 0
                        profit += temp_profit

            if current_bar["fast_ema"] > current_bar["slow_ema"] and last_bar["fast_ema"] <= last_bar["slow_ema"]:
                if not has_long:
                    if long_size == 0 and long_price == 0:
                        long_size = 1
                        long_price = current_bar["Close"]
                        long_count += 1
                        long_index = i

            if current_bar["fast_ema"] < current_bar["slow_ema"] and last_bar["fast_ema"] >= last_bar["slow_ema"]:
                if not has_short:
                    if short_size == 0 and short_price == 0:
                        short_size = 1
                        short_price = current_bar["Close"]
                        short_count += 1
                        short_index = i

        print("long_count:", long_count, "short_count:", short_count,  "profit:", profit,
              "real_profile:", (profit - (long_count + short_count) * fee_rate * 2))



if __name__ == "__main__":
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    s = "BTC-USD"
    p = "1min"
    c = 2000
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MatPlot.get_data(s, p, c))
    loop.close()
