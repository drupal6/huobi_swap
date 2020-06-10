from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
from utils.config import config
from utils.recordutil import record

if __name__ == '__main__':
    config.loads("../config/btc-config.json")
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxxx")

    async def get_data():
        success, error = await request.get_trades(contract_type="BTC-USD", size=2000)
        if error:
            print(error)
        for datas in success["data"]:
            for tick in datas["data"]:
                record.record_trade(symbol="BTC-USD", tick=tick, init=True)
        record.init = True

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







