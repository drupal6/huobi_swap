from api.huobi.huobi_request_swap import HuobiSwapRequest
from api.huobi.huobi_request import HuobiRequest
import asyncio
from utils.config import config
from utils.recordutil import record
import pandas as pd
import talib
pd.set_option("expand_frame_repr", False)
pd.set_option("display.max_rows", None)


if __name__ == '__main__':
    config.loads("../config/btc-config.json")
    request = HuobiRequest("https://api.btcgateway.pro", "xxxx", "xxxxx")

    async def get_data():
        success, error = await request.get_info(symbol="BTC", contract_type="quarter")
        if error:
            print(error)
        if success:
            print(success)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







