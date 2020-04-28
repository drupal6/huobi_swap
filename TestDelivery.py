from api.huobi.huobi_request_swap import HuobiSwapRequest
from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio
from utils.config import config
from utils.dingding_msg_util import MsgUtil
from utils.dingding import DingTalk

if __name__ == '__main__':
    config.loads("config/btc-swap-config.json")
    DingTalk.send_text_msg(content="test")
    # request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    #
    # async def get_data():
    #     success, error = await request.get_info(contract_code="BTC-USD")
    #     print(success)
    #     print(error)
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_data())
    # loop.close()







