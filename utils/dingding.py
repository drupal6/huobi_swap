# -*- coding:utf-8 -*-

"""
DingTalk Bot API.
"""

from api.utils.request import AsyncHttpRequests
from utils import logger
import requests
import json
from requests import Response
from enum import Enum
import time
import hmac
import hashlib
import base64
import urllib.parse
from utils.config import config


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"

class DingTalk:
    """ DingTalk Bot API.
    """
    BASE_URL = "https://oapi.dingtalk.com/robot/send?access_token=%s&timestamp=%s&sign=%s"

    @classmethod
    def send_text_msg(cls, content, phones=None, is_at_all=False):
        """ Send text message.

        Args:
            access_token: DingTalk Access Token.
            content: Message content to be sent.
            phones: Phone numbers to be @.
            is_at_all: Is @ all members? default is False.
        """
        content = "msg:" + content
        body = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        if is_at_all:
            body["at"] = {"isAtAll": True}
        if phones:
            assert isinstance(phones, list)
            body["at"] = {"atMobiles": phones}
        timestamp, sign = cls._sign()
        access_token = config.dingding.get("access_token")
        url = cls.BASE_URL % (access_token, timestamp, sign)
        cls._request(url=url, method=RequestMethod.POST, body=body)

    @classmethod
    def send_markdown_msg(cls, access_token, title, text, phones=None, is_at_all=False):
        """ Send markdown message.

        Args:
            access_token: DingTalk Access Token.
            title: Message title.
            text: Message content to be sent.
            phones: Phone numbers to be @.
            is_at_all: Is @ all members? default is False.
        """
        text = "msg:" + text
        body = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }
        if is_at_all:
            body["at"] = {"isAtAll": True}
        if phones:
            assert isinstance(phones, list)
            body["at"] = {"atMobiles": phones}
        url = cls.BASE_URL + access_token
        cls._request(url=url, method=RequestMethod.POST, body=body)

    @classmethod
    def _request(self, url, method: RequestMethod, params=None, body=None):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)
        response: Response = requests.request(method.value, url, headers=headers, params=params, data=data,
                                              timeout=30)
        json_data = response.json()
        if response.status_code == 200:
            return json_data
        else:
            raise Exception(f"请求{url}的数据发生了错误：{json_data}")

    @classmethod
    def _sign(cls):
        timestamp = str(round(time.time() * 1000))
        secret = config.dingding.get("secret")
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

