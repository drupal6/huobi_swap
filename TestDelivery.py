from api.huobi.huobi_request_swap import HuobiSwapRequest
from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio

if __name__ == '__main__':
    request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")

    async def get_data():
        success, error = await request.get_klines(contract_type="BTC-USD", period="5min", size=200)
        print(success)
        print(error)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







