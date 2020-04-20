# -*- coding:utf-8 -*-

"""
Huobi Swap Api Module.
"""

import gzip
import json
import copy
import hmac
import base64
import urllib
import hashlib
import datetime
import time
from urllib.parse import urljoin
from api.utils.request import AsyncHttpRequests


__all__ = ("HuobiRequest", )

class HuobiRequest:
    """ Huobi Swap REST API Client.

    Attributes:
        host: HTTP request host.
        access_key: Account's ACCESS KEY.
        secret_key: Account's SECRET KEY.
        passphrase: API KEY Passphrase.
    """

    def __init__(self, host, access_key, secret_key):
        """ initialize REST API client. """
        self._host = host
        self._access_key = access_key
        self._secret_key = secret_key

    async def get_trade_info(self, symbol, size=200):
        """
        批量获取交易数据
        :param symbol:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        :param size:[1, 2000]
        :return:
        """
        uri = "/market/history/trade"
        params = {
            "symbol": symbol,
            "size": size
        }
        success, error = await self.request("GET", uri, params)
        return success, error

    async def get_delivery_info(self, symbol=None, contract_type=None, contract_code=None):
        """
        合约信息
        :param symbol: "BTC","ETH"...
        :param contract_type: 合约类型 (当周:"this_week", 次周:"next_week", 季度:"quarter")
        :param contract_code: BTC180914 ...
        :return:
        """
        uri = "/api/v1/contract_contract_info"
        params = {}
        if symbol:
            params["symbol"] = symbol
        if contract_type:
            params["contract_type"] = contract_type
        if contract_code:
            params["contract_code"] = contract_code
        success, error = await self.request("GET", uri, params)
        return success, error

    async def get_klines(self, contract_type, period="1min", size=150, _from=None, _to=None):
        """
        获取k先数据
        :param contract_type:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        :param period:1min, 5min, 15min, 30min, 60min,4hour,1day, 1mon
        :param size:[1,2000]
        :param _from:开始时间戳 10位 单位S
        :param _to:结束时间戳 10位 单位S
        :return:
        """
        uri = "/market/history/kline"
        params = {
            "symbol": contract_type,
            "period": period,
            "size": size
        }
        if _from and _to:
            params["from"] = _from
            params["_to"] = _to
        success, error = await self.request("GET", uri, params=params)
        return success, error

    async def get_price_limit(self, symbol=None, contract_type=None, contract_code=None):
        """
        获取荷叶最高限价和最低限价
        :param symbol:"BTC","ETH"...
        :param contract_type:合约类型 (当周:"this_week", 次周:"next_week", 季度:"quarter")
        :param contract_code:BTC180914 ...
        :return:
        """
        uri = "/api/v1/contract_price_limit"
        params = {}
        if symbol:
            params["symbol"] = symbol
        if contract_type:
            params["contract_type"] = contract_type
        if contract_code:
            params["contract_code"] = contract_code
        success, error = await self.request("GET", uri, params=params)
        return success, error

    async def get_orderbook(self, symbol, type):
        """
        获取行情深度数据
        :param symbol:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        :param type:获得150档深度数据，使用step0, step1, step2, step3, step4, step5（step1至step5是进行了深度合并后的深度），
        使用step0时，不合并深度获取150档数据;获得20档深度数据，使用 step6, step7, step8, step9, step10, step11
        （step7至step11是进行了深度合并后的深度），使用step6时，不合并深度获取20档数据
        :return:
        """
        uri = "/market/depth"
        params = {
            "symbol": symbol,
            "type": type
        }
        success, error = await self.request("GET", uri, params=params)
        return success, error

    async def get_asset_info(self, symbol=None):
        """
        获取用户账号信息
        :param symbol:"BTC","ETH"...如果缺省，默认返回所有品种
        :return:
        """
        uri = "/api/v1/contract_account_info"
        body = {}
        if symbol:
            body["symbol"] = symbol
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def get_position(self, symbol=None):
        """
        获取用户持仓信息
        :param symbol:"BTC","ETH"...如果缺省，默认返回所有品种
        :return:
        """
        uri = "/api/v1/contract_position_info"
        body = {}
        if symbol:
            body["symbol"] = symbol
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def create_order(self, symbol, contract_type, contract_code, volume, direction, offset, lever_rate,
                           order_price_type, client_order_id=None, price=None):
        """
        合约下单
        :param symbol:"BTC","ETH"...
        :param contract_type:合约类型 ("this_week":当周 "next_week":下周 "quarter":季度)
        :param contract_code:BTC180914
        :param volume:委托数量(张)
        :param direction:"buy":买 "sell":卖
        :param offset:"open":开 "close":平
        :param lever_rate:杠杆倍数[“开仓”若有10倍多单，就不能再下20倍多单]
        :param order_price_type:订单报价类型 "limit":限价 "opponent":对手价 "post_only":只做maker单,
        post only下单只受用户持仓数量限制,optimal_5：最优5档、optimal_10：最优10档、
        optimal_20：最优20档，ioc:IOC订单，fok：FOK订单
        :param client_order_id:客户自己填写和维护，必须为数字
        :param price:价格
        :return:
        """
        uri = "/api/v1/contract_order"
        body = {
            "symbol": symbol,
            "contract_type": contract_type,
            "contract_code": contract_code,
            "volume": volume,
            "direction": direction,
            "offset": offset,
            "lever_rate": lever_rate,
            "order_price_type": order_price_type
        }
        if client_order_id:
            body.update({"client_order_id": client_order_id})
        if price:
            body.update({"price": price})
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error
    
    async def create_orders(self, orders_data):
        """ Batch Create orders.
            orders_data = {'orders_data': [
               {  
                'symbol':'BCH',  'contract_type':'','contract_code':''
                'volume':1, 'direction':1, 'offset':'buy', 'lever_rate':'open',
                'orderPriceType':20, 'client_order_id':'false， 'price':false},
                {
                'symbol':'BCH',  'contract_type':'','contract_code':''
                'volume':1, 'direction':1, 'offset':'buy', 'lever_rate':'open',
                'orderPriceType':20, 'client_order_id':'false， 'price':false}]}
        """
        uri = "/api/v1/contract_batchorder"
        body = orders_data
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def revoke_orders(self, symbol, order_id=None, client_order_id=None):
        """
        撤销订单 order_id和client_order_id必须有1个有值
        :param order_id:订单ID(多个订单ID中间以","分隔,一次最多允许撤消20个订单)
        :param client_order_id:客户订单ID(多个订单ID中间以","分隔,一次最多允许撤消20个订单)
        :param symbol:"BTC","ETH"...
        :return:
        """
        uri = "/api/v1/contract_cancel"
        body = {
            "symbol": symbol
        }
        if order_id:
            body["order_id"] = order_id
        elif client_order_id:
            body["client_order_id"] = client_order_id
        else:
            return None, "order_id and client_order_id is None"
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def revoke_order_all(self, symbol, contract_code=None, contract_type=None):
        """
        全部撤销
        :param contract_type:合约类型 ("this_week":当周 "next_week":下周 "quarter":季度)
        :param contract_code:BTC180914
        :return:
        """
        uri = "/api/v1/contract_cancelall"
        body = {
            "symbol": symbol,
        }
        if contract_code:
            body["contract_code"] = contract_code
        if contract_type:
            body["contract_type"] = contract_type
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def get_order_info(self, symbol, order_id=None, client_order_id=None):
        """
        获取合约订单信息
        :param symbol:"BTC","ETH"...
        :param order_id:订单ID(多个订单ID中间以","分隔,一次最多允许查询50个订单)
        :param client_order_id:客户订单ID(多个订单ID中间以","分隔,一次最多允许查询50个订单)
        :return:
        """
        uri = "/api/v1/contract_order_info"
        body = {
            "symbol": symbol
        }
        if order_id:
            body["order_id"] = order_id
        elif client_order_id:
            body["client_order_id"] = client_order_id
        else:
            return None, "order_id and client_order_id is None"
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def get_open_orders(self, symbol, page_index=1, page_size=20):
        """
        获取合约当前未成交委托
        :param symbol:"BTC","ETH"...
        :param page_index:页码，不填默认第1页
        :param page_size:不填默认20，不得多于50
        :return:
        """
        uri = "/api/v1/contract_openorders"
        body = {
            "symbol": symbol,
            "page_index": page_index,
            "page_size": page_size
        }
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error
    
    async def get_history_orders(self, symbol, trade_type, stype, status, create_date, page_index=1, page_size=20,
                                    contract_code=None, order_type=None):
        """
        获取合约历史委托
        :param symbol:"BTC","ETH"...
        :param trade_type:0:全部,1:买入开多,2: 卖出开空,3: 买入平空,4: 卖出平多,5: 卖出强平,6: 买入强平,7:交割平多,8: 交割平空
        :param stype:1:所有订单,2:结束状态的订单
        :param status:0:全部,3:未成交, 4: 部分成交,5: 部分成交已撤单,6: 全部成交,7:已撤单
        :param create_date:可随意输入正整数, ，如果参数超过90则默认查询90天的数据
        :param page_index:页码，不填默认第1页
        :param page_size:每页条数，不填默认20 不得多于50
        :param contract_code:合约代码BTC180914
        :param order_type:1：限价单、3：对手价、4：闪电平仓、5：计划委托、6：post_only、7：最优5档、8：最优10档、9：最优20档、10：fok、11：ioc
        :return:
        """
        uri = "/api/v1/contract_hisorders"
        body = {
            "symbol": symbol,
            "trade_type": trade_type,
            "type": stype,
            "status": status,
            "create_date": create_date,
            "page_index": page_index,
            "page_size": page_size
        }
        if contract_code:
            body["contract_code"] = contract_code
        if order_type:
            body["order_type"] = order_type
        success, error = await self.request("POST", uri, body=body, auth=True)
        return success, error

    async def get_merged(self, contract_type, ):
        """
        获取k先数据
        :param contract_type:如"BTC_CW"表示BTC当周合约，"BTC_NW"表示BTC次周合约，"BTC_CQ"表示BTC季度合约
        :return:
        """
        uri = "/market/detail/merged"
        params = {
            "symbol": contract_type,
        }
        success, error = await self.request("GET", uri, params=params)
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
