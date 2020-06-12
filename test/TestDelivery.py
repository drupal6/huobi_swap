from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
from utils.config import config
from utils.recordutil import record
import pandas as pd
import talib
pd.set_option("expand_frame_repr", False)
pd.set_option("display.max_rows", None)


if __name__ == '__main__':
    config.loads("../config/btc-config.json")
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxxx")

    async def get_data():
        success, error = await request.get_klines(contract_type="BTC-USD",)
        if error:
            print(error)
        history_klines = success.get("data")
        df = pd.DataFrame(history_klines, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                   'high': 6, 'amount': 7})
        df = df[['id', 'open', 'high', 'low', 'close', 'amount']]
        df["max_close"] = talib.MAX(df["close"], 9)
        df["min_close"] = talib.MIN(df["close"], 9)
        print(df)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







