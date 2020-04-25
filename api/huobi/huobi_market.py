# -*— coding:utf-8 -*-

"""
Huobi Swap Market Server.
"""

import gzip
import json
import time

from utils import logger
from api.utils.websocket import Websocket
from api.huobi.sub.base_sub import BaseSub
from api.model.tasks import SingleTask
from api.model.error import Error


class HuobiMarket(Websocket):

    def __init__(self, **kwargs):
        e = None
        if not kwargs.get("platform"):
            e = Error("platform miss")
        if not kwargs.get("connected_callback"):
            e = Error("connected_callback miss")
        if not kwargs.get("process_binary"):
            e = Error("process_binary miss")
        if e:
            logger.error(e, caller=self)
            return
        self._platform = kwargs.get("platform")
        self._wss = kwargs.get("wss", "wss://www.hbdm.com")
        self._connected_callback = kwargs.get("connected_callback")
        self._process_binary = kwargs.get("process_binary")
        if self._platform == "swap":
            url = self._wss + "/swap-ws"
        else:
            url = self._wss + "/ws"
        super(HuobiMarket, self).__init__(url, send_hb_interval=5)
        self.initialize()

    async def _send_heartbeat_msg(self, *args, **kwargs):
        """ 发送心跳给服务器
        """
        if not self.ws:
            logger.warn("websocket connection not connected yet!", caller=self)
            return
        data = {"pong": int(time.time()*1000)}
        await self.ws.send_json(data)

    async def connected_callback(self):
        """
        链接成功
        """
        SingleTask.run(self._connected_callback)

    async def add_sub(self, sub: BaseSub):
        sub_data = sub.sub_data()
        if sub_data:
            await self.ws.send_json(sub_data)

    async def process_binary(self, msg):
        data = json.loads(gzip.decompress(msg).decode())
        logger.debug("data:", json.dumps(data), caller=self)
        channel = data.get("ch")
        if not channel:
            if data.get("ping"):
                hb_msg = {"pong": data.get("ping")}
                await self.ws.send_json(hb_msg)
            return
        await self._process_binary(channel, data)

    async def _send_heartbeat_msg(self, *args, **kwargs):
        """ 发送心跳给服务器
        """
        if not self.ws:
            logger.warn("websocket connection not connected yet!", caller=self)
            return
        data = {"pong": int(time.time()*1000)}
        await self.ws.send_json(data)