# -*- coding:utf-8 -*-

"""
Huobi Swap Api Module.
"""

import json
import hmac
import base64
import urllib
import hashlib
import datetime
from urllib.parse import urljoin
from api.utils.request import AsyncHttpRequests


__all__ = ("HuobiRequestSpot", )


class HuobiRequestSpot:
    """ Huobi Spot REST API Client.

    Attributes:
        host: HTTP request host.
        access_key: Account's ACCESS KEY.
        secret_key: Account's SECRET KEY.
        passphrase: API KEY Passphrase.
    """

    def __init__(self, host, access_key, secret_key):
        """ initialize REST API client. """
        self._host = host  # https://api.huobi.pro
        self._access_key = access_key
        self._secret_key = secret_key

    async def get_ticker(self, symbol):
        """
        聚合行情（Ticker）
        :param symbol:交易对	btcusdt, ethbtc...（取值参考GET /v1/common/symbols）
        :return:
        """
        uri = "/market/detail/merged"
        params = {
            "symbol": symbol,
        }
        success, error = await self.request("GET", uri, params)
        return success, error

    async def get_accounts(self):
        """
        查询当前用户的所有账户 ID account-id 及其相关信息
        :return:
        """
        uri = "/v1/account/accounts"
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def get_symbols(self):
        """
        此接口返回所有火币全球站支持的交易对
        :return:
        """
        uri = "/v1/common/symbols"
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def get_order(self, order_id):
        """
        此接口返回指定订单的最新状态和详情。通过API创建的订单，撤销超过2小时后无法查询
        :param order_id:订单ID，填在path中
        :return:
        """
        uri = "/v1/order/orders/%s" % order_id
        success, error = await self.request("GET", uri, auth=True)
        return success, error

    async def place_order(self, account_id, symbol, type, amount, price, source=None, client_order_id=None,
                          stop_price=None, operator=None):
        """
        下单
        :param account_id:账户 ID，取值参考 GET /v1/account/accounts。现货交易使用 ‘spot’ 账户的 account-id；逐仓杠杆交易，请使用 ‘margin’ 账户的 account-id；全仓杠杆交易，请使用 ‘super-margin’ 账户的 account-id
        :param symbol:交易对,即btcusdt, ethbtc...（取值参考GET /v1/common/symbols）
        :param type:订单类型，包括buy-market, sell-market, buy-limit, sell-limit, buy-ioc, sell-ioc, buy-limit-maker, sell-limit-maker（说明见下文）, buy-stop-limit, sell-stop-limit, buy-limit-fok, sell-limit-fok, buy-stop-limit-fok, sell-stop-limit-fok
        :param amount:订单交易量（市价买单为订单交易额）
        :param price:订单价格（对市价单无效）
        :param source:现货交易填写“spot-api”，逐仓杠杆交易填写“margin-api”，全仓杠杆交易填写“super-margin-api”, C2C杠杆交易填写"c2c-margin-api"
        :param client_order_id:用户自编订单号（最大长度64个字符，须在24小时内保持唯一性）
        :param stop_price:止盈止损订单触发价格
        :param operator:止盈止损订单触发价运算符 gte – greater than and equal (>=), lte – less than and equal (<=)
        buy-limit-maker
        当“下单价格”>=“市场最低卖出价”，订单提交后，系统将拒绝接受此订单；
        当“下单价格”<“市场最低卖出价”，提交成功后，此订单将被系统接受。
        sell-limit-maker
        当“下单价格”<=“市场最高买入价”，订单提交后，系统将拒绝接受此订单；
        当“下单价格”>“市场最高买入价”，提交成功后，此订单将被系统接受。
        :return:
        """
        uri = "/api/v1/contract_order"
        body = {
            "account_id": account_id,
            "symbol": symbol,
            "type": type,
            "amount": amount,
            "price": price,
        }
        if source:
            body.update({"source": source})
        if client_order_id:
            body.update({"client_order_id": client_order_id})
        if stop_price:
            body.update({"stop_price": stop_price})
        if operator:
            body.update({"operator": operator})
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def cancel_order(self, order_id):
        """
        撤销订单
        :param order_id:
        :return:
        """
        uri = "/v1/order/orders/%s/submitcancel" % order_id
        success, error = await self.request("POST", uri, auth=True)
        return success, error

    async def get_open_orders(self, account_id, symbol, side=None, form=None, direct=None, size=None):
        """
        查询当前未成交订单
        :param account_id:账户 ID，取值参考 GET /v1/account/accounts。现货交易使用‘spot’账户的 account-id；逐仓杠杆交易，请使用 ‘margin’ 账户的 account-id；全仓杠杆交易，请使用 ‘super-margin’ 账户的 account-id；c2c杠杆交易，请使用borrow账户的account-id
        :param symbol:交易对,即btcusdt, ethbtc...（取值参考GET /v1/common/symbols）
        :param side:指定只返回某一个方向的订单，可能的值有: buy, sell. 默认两个方向都返回。
        :param form:查询起始 ID，如果是向后查询，则赋值为上一次查询结果中得到的最后一条id ；如果是向前查询，则赋值为上一次查询结果中得到的第一条id
        :param direct:查询方向，prev 向前；next 向后
        :param size:返回订单的数量，最大值500。
        :return:
        """
        uri = "/v1/order/openOrders"
        body = {
            "account_id": account_id,
            "symbol": symbol,
            "side": type
        }
        if side:
            body.update({"side": side})
        if form:
            body.update({"from": form})
        if direct:
            body.update({"direct": direct})
        if size:
            body.update({"size": size})
        success, error = await self.request("GET", uri, body=body, auth=True)
        return success, error

    async def request(self, method, uri, params=None, body=None, headers=None, auth=False):
        """ Do HTTP request.

        Args:
            method: HTTP request method. `GET` / `POST` / `DELETE` / `PUT`.
            uri: HTTP request uri.
            params: HTTP query params.
            body: HTTP request body.
            headers: HTTP request headers.
            auth: If this request requires authentication.

        Returns:
            success: Success results, otherwise it's None.
            error: Error information, otherwise it's None.
        """
        url = urljoin(self._host, uri)

        if auth:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            params = params if params else {}
            params.update({"AccessKeyId": self._access_key,
                           "SignatureMethod": "HmacSHA256",
                           "SignatureVersion": "2",
                           "Timestamp": timestamp})

            params["Signature"] = self.generate_signature(method, params, uri)

        if not headers:
            headers = {}
        if method == "GET":
            headers["Content-type"] = "application/x-www-form-urlencoded"
            headers["User-Agent"] = "AlphaQuant1.0.0_200110_alpha"
            _, success, error = await AsyncHttpRequests.fetch("GET", url, params=params, headers=headers, timeout=10)
        else:
            headers["Accept"] = "application/json"
            headers["Content-type"] = "application/json"
            headers["User-Agent"] = "AlphaQuant1.0.0_200110_alpha"
            _, success, error = await AsyncHttpRequests.fetch("POST", url, params=params, data=body, headers=headers,
                                                              timeout=10)
        if error:
            return None, error
        if not isinstance(success, dict):
            result = json.loads(success)
        else:
            result = success
        if result.get("status") != "ok":
            return None, result
        return result, None

    def generate_signature(self, method, params, request_path):
        host_url = urllib.parse.urlparse(self._host).hostname.lower()
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
