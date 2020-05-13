from api.huobi.huobi_request_swap import HuobiSwapRequest
import asyncio

if __name__ == '__main__':
    p = {"lever_rate": 50}
    print(p.get("lever_rate", 20))
    # request = HuobiSwapRequest("https://api.btcgateway.pro", "xxxx", "xxxx")
    #
    # async def get_data():
    #     success, error = await request.create_order(contract_code="BTC-USD", price=10000, quantity=1, direction="sell",
    #                                                 offset="open", lever_rate=50, order_price_type="limit")
    #     print(success)
    #     print(error)
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_data())
    # loop.close()







