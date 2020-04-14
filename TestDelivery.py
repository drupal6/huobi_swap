from api.huobi.huobi_request import HuobiRequest
import asyncio
from utils.tools import round_to

if __name__ == '__main__':
    request = HuobiRequest("https://api.btcgateway.pro", "d1a345a1-9d985a5b-dqnh6tvdf3-87328", "5c367063-a7895a13-bcfdd1a5-276f2")

    async def get_data():
        success, error = await request.get_delivery_info(symbol="EOS", contract_type="this_week", contract_code="")
        print(success)
        print(error)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data())
    loop.close()







