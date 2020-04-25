# -*- coding:utf-8 -*-

"""
Huobi Swap Api Module.

Author: QiaoXiaofeng
Date:   2020/01/10
Email:  andyjoe318@gmail.com
"""

import gzip
import json
import copy
import datetime
import time
import urllib
import hmac
import base64
import urllib
import hashlib
import datetime
import time
from urllib.parse import urljoin
from api.utils.websocket import Websocket
from api.model.error import Error
from api.model.tasks import SingleTask
from utils import logger
from api.utils.decorator import async_method_locker
from api.huobi.sub.base_sub import BaseSub

__all__ = ("HuobiTrade",)


class HuobiTrade(Websocket):

    def __init__(self, **kwargs):
        """Initialize."""
        e = None
        if not kwargs.get("wss"):
            kwargs["wss"] = "wss://api.hbdm.com"
        if not kwargs.get("platform"):
            e = Error("param platform miss")
        if not kwargs.get("access_key"):
            e = Error("param access_key miss")
        if not kwargs.get("secret_key"):
            e = Error("param secret_key miss")
        if not kwargs.get("process_binary"):
            e = Error("process_binary miss")
        if e:
            logger.error(e, caller=self)
            return

        self._platform = kwargs.get("platform")
        self._wss = kwargs.get("wss")
        self._access_key = kwargs.get("access_key")
        self._secret_key = kwargs.get("secret_key")
        self._process_binary = kwargs.get("process_binary")
        if self._platform == "swap":
            url = self._wss + "/swap-notification"
        else:
            url = self._wss + "/notification"
        super(HuobiTrade, self).__init__(url, send_hb_interval=5)
        self.initialize()

    async def add_sub(self, sub: BaseSub):
        data = sub.sub_data()
        if data:
            await self.ws.send_json(sub.sub_data())

    async def _reconnect(self):
        await super(HuobiTrade, self)._reconnect()

    async def _send_heartbeat_msg(self, *args, **kwargs):
        data = {"pong": int(time.time() * 1000)}
        if not self.ws:
            logger.error("Websocket connection not yeah!", caller=self)
            return
        await self.ws.send_json(data)

    async def connected_callback(self):
        """After connect to Websocket server successfully, send a auth message to server."""
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        data = {
            "AccessKeyId": self._access_key,
            "SignatureMethod": "HmacSHA256",
            "SignatureVersion": "2",
            "Timestamp": timestamp
        }
        if self._platform == "swap":
            sign = self.generate_signature("GET", data, "/swap-notification")
        else:
            sign = self.generate_signature("GET", data, "/notification")
        data["op"] = "auth"
        data["type"] = "api"
        data["Signature"] = sign
        await self.ws.send_json(data)

    def generate_signature(self, method, params, request_path):
        host_url = urllib.parse.urlparse(self._wss).hostname.lower()
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode(encoding="UTF8")
        secret_key = self._secret_key.encode(encoding="utf8")
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    @async_method_locker("HuobiTrade.process_binary.locker")
    async def process_binary(self, raw):
        """ 处理websocket上接收到的消息
        @param raw 原始的压缩数据
        """
        data = json.loads(gzip.decompress(raw).decode())
        logger.debug("data:", data, caller=self)
        op = data.get("op")
        if op == "ping":
            hb_msg = {"op": "pong", "ts": data.get("ts")}
            await self.ws.send_json(hb_msg)
        else:
            await self._process_binary(op, data)





