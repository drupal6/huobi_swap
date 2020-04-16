from api.huobi.huobi_request import HuobiRequest
import asyncio
from utils.tools import round_to

if __name__ == '__main__':
    request = HuobiRequest("https://api.btcgateway.pro", "xxxxxx", "xxxxxx")

    async def get_data():
        success, error = await request.get_klines(symbol="EOS", contract_type="this_week", contract_code="")
        print(success)
        print(error)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







