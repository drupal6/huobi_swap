from api.huobi.huobi_market import HuobiMarket
from api.huobi.sub.base_sub import BaseSub
from utils import logger
from api.huobi.huobi_request import HuobiRequest


class Market:
    """
    市场对象
    """
    def __init__(self, platform="", wss=None, request: HuobiRequest = None):
        self._platform = platform
        self._wss = wss
        self._request = request
        self._channel_sub = {}
        self._m = None

    def start(self):
        mm = {
            "platform": self._platform,
            "wss": self._wss,
            "connected_callback": self.connected_callback,
            "process_binary": self.process_binary
        }
        self._m = HuobiMarket(**mm)

    def add_sub(self, sub: BaseSub):
        """
        添加订阅
        :param sub:
        :return:
        """
        self._channel_sub[sub.topic()] = sub

    async def connected_callback(self):
        print("connected_callback")
        """
        链接成功后订阅消息
        :return:
        """
        for sub in self._channel_sub.values():
            await self._m.add_sub(sub)

    async def process_binary(self, channel, data):
        """
        处理市场返回消息
        :param channel:
        :param data:
        :return:
        """
        topic = channel.lower()
        sub = self._channel_sub.get(topic, None)
        if sub:
            await sub.call_back(channel, data)
        else:
            logger.error("event error! channel:", channel, "data:", data, caller=self)

