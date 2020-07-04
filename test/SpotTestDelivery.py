from api.huobi.huobi_request_spot import HuobiRequestSpot
import asyncio
from utils.config import config
from utils.recordutil import record
import pandas as pd
import talib
pd.set_option("expand_frame_repr", False)
pd.set_option("display.max_rows", None)
from utils.tools import round_to

if __name__ == '__main__':
    config.loads("../config/btc-config.json")
    request = HuobiRequestSpot("https://api.huobi.pro", "xxxxxx", "xxxxxx")

    async def get_data():
        success, error = await request.get_balance("4120119")
        if error:
            print(error)
        if success:
            print(success)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







