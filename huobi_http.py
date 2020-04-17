import requests
from datetime import datetime
from enum import Enum
import hmac
import hashlib
import base64
from urllib.parse import urlencode, quote
import json
from requests import Response
import pandas as pd
pd.set_option("expand_frame_repr", False)
import time
import talib


class HuobiPeriod(Enum):
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "60min"
    DAY_1 = "1day"
    WEEK_1 = "1week"
    YEAR_1 = "1year"


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class HuobiHttpClient(object):
    """
    火币http client 公开和签名的接口.
    """

    def __init__(self, host=None, key=None, secret=None, timeout=5):
        self.host = host if host else "https://api.huobi.br.com"   # https://api.huobi.br.com # https://api.huobi.co
        self.api_host = 'api.huobi.br.com'  # api.huobi.br.com
        self.key = key
        self.secret = secret
        self.timeout = timeout

    def _request(self, method: RequestMethod, path, params=None, body=None, verify=False):

        url = self.host + path
        if params and not verify:
            url = url + '?' + self._build_params(params)
        if verify:
            sign_data = self._sign(method.value, path, params)
            url = url + '?' + self._build_params(sign_data)
        headers = {"Content-Type": "application/json"}

        # print(url)
        data = json.dumps(body)

        response: Response = requests.request(method.value, url, headers=headers, data=data, timeout=self.timeout)
        json_data = response.json()

        if response.status_code == 200 and json_data['status'] == 'ok':
            return json_data['data']
        else:
            raise Exception(f"请求{url}的数据发生了错误：{json_data}")

    def get_time_stamp(self):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    def _build_params(self, params: dict):
        """
        构造query string
        :param params:
        :return:
        """
        return '&'.join([f"{key}={params[key]}" for key in params.keys()])

    def get_symbols(self):
        """
        此接口返回所有火币全球站支持的交易对。
        :return:
        """
        path = "/v1/common/symbols"

        # url = self.host + path
        # json_data = requests.get(url, timeout=self.timeout).json()
        # if json_data['status'] == 'ok':
        #     return json_data['data']
        #
        # raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        return self._request(RequestMethod.GET, path)

    def get_currencys(self):
        """
        此接口返回所有火币全球站支持的币种。
        :return:
        """
        path = "/v1/common/currencys"
        # url = self.host + path
        # json_data = requests.get(url, timeout=self.timeout).json()
        # if json_data['status'] == 'ok':
        #     return json_data['data']
        #
        # raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        return self._request(RequestMethod.GET, path)

    def get_exchange_timestamp(self):

        path = "/v1/common/timestamp"
        # url = self.host + path
        # json_data = requests.get(url, timeout=self.timeout).json()
        # if json_data['status'] == 'ok':
        #     return json_data['data']
        #
        # raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        return self._request(RequestMethod.GET, path)

    def get_kline_data(self, symbol: str, period:HuobiPeriod, size=2000):
        path = "/market/history/kline"
        params = {"symbol": symbol, "period": period.value, "size": size}

        # url = self.host + path
        # url = url + '?' + self._build_params(params)
        # print(url)
        # exit()
        # json_data = requests.get(url, params=params, timeout=self.timeout).json()
        # # json_data = requests.get(url, timeout=self.timeout).json()
        # if json_data['status'] == 'ok':
        #     return json_data['data']
        #
        # raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # 优化后的代码.
        return self._request(RequestMethod.GET, path, params=params)

    def get_tickers(self):
        path = "/market/tickers"

        url = self.host + path
        json_data = requests.get(url, timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']

        # return json_data
        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.GET, path)

    def get_ticker(self, symbol=None, depth=5, type='step0'):
        """
        :param symbol: btcusdt  orderbook
        :param depth: value should be: 5 10  20
        :param type: step0 step1 step2 step3 step 4 step5
        :return: 返回ticker数据
        """

        path = "/market/depth"
        url = self.host + path
        params = {"symbol": symbol, 'depth': depth, "type": type}
        json_data = requests.get(url, params=params, timeout=self.timeout).json()
        # print(json_data)
        if json_data['status'] == 'ok':
            return json_data['tick']
        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.GET, path, params=params)

    def get_market_detail(self, symbol):
        path = "/market/detail"
        url = self.host + path
        params = {"symbol": symbol}
        json_data = requests.get(url, params=params, timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['tick']
        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.GET, path, params=params)

    ######################## private data ###################


    def _sign(self, method, path, params=None):

        """
        该方法为签名的方法
        :return:
        """
        sorted_params = [
            ("AccessKeyId", self.key),
            ("SignatureMethod", "HmacSHA256"),
            ("SignatureVersion", "2"),
            ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
        ]

        if params:
            sorted_params.extend(list(params.items()))
            sorted_params = list(sorted(sorted_params))

        encode_params = urlencode(sorted_params)

        payload = [method, self.api_host, path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode(encoding="UTF8")
        secret_key = self.secret.encode(encoding="UTF8")
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode("UTF8")
        sign_params = dict(sorted_params)  # header key  # 路径。
        sign_params["Signature"] = quote(signature) # uri
        return sign_params

    def get_accounts(self):

        """
        获取账户信息的方法.
         [{'id': 897261, 'type': 'spot', 'subtype': '', 'state': 'working'},
         {'id': 6703531, 'type': 'margin', 'subtype': 'adausdt', 'state': 'working'},
          {'id': 7070883, 'type': 'margin', 'subtype': 'bsvusdt', 'state': 'working'},
          {'id': 5157717, 'type': 'margin', 'subtype': 'btmusdt', 'state': 'working'},
          {'id': 7471276, 'type': 'margin', 'subtype': 'ethusdt', 'state': 'working'},
          {'id': 5153600, 'type': 'margin', 'subtype': 'ontusdt', 'state': 'working'},
          {'id': 6290114, 'type': 'margin', 'subtype': 'xrpusdt', 'state': 'working'},
          {'id': 3214863, 'type': 'otc', 'subtype': '', 'state': 'working'},
          {'id': 3360132, 'type': 'point', 'subtype': '', 'state': 'working'}]
        :return:
        """

        path = "/v1/account/accounts"

        sign_data = self._sign('GET', path)
        url = self.host + path
        url += '?' + self._build_params(sign_data)
        # print(url)
        # exit()
        json_data = requests.get(url, headers={'Content-Type': 'application/json'}, timeout=self.timeout).json()
        # json_data = requests.get(url, timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']

        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.GET, path, verify=True)

    def get_account_balance(self, account_id):
        """
        查询指定账户的余额，支持以下账户：
        spot：现货账户， margin：杠杆账户，otc：OTC 账户，point：点卡账户
        :param account_id:
        :return:
        """
        path = f'/v1/account/accounts/{account_id}/balance'
        print(path)
        # exit()
        url = self.host + path
        sign_data = self._sign('GET', path)
        # print(sign_data)
        url += '?' + self._build_params(sign_data)
        print(url)
        # exit()
        json_data = requests.get(url, timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']
        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.GET, path, verify=True)

    def place_order(self, account_id, symbol, type, amount, price=None, source='api', stop_price=None, operator=None):
        """

        :param account_id: 账户 ID，使用 GET /v1/account/accounts 接口查询。现货交易使用 ‘spot’ 账户的 account-id；杠杆交易，请使用 ‘margin’ 账户的 account-id
        :param symbol: 交易对, 例如btcusdt, ethbtc
        :param type: 订单类型，包括buy-market, sell-market, buy-limit, sell-limit, buy-ioc, sell-ioc, buy-limit-maker, sell-limit-maker（说明见下文）, buy-stop-limit, sell-stop-limit
        :param amount: 订单交易量（市价买单此字段为订单交易额）
        :param price: limit order的交易价格
        :param source: 止盈止损订单触发价格
        :param stop_price: 止盈止损订单触发价格
        :param operator: 止盈止损订单触发价运算符 gte – greater than and equal (>=), lte – less than and equal (<=)
        :return:
        """
        path = "/v1/order/orders/place"

        body = {'account-id': account_id,
                'symbol': symbol,
                'type':  type,
                'amount': str(amount),
                'source': source
                }

        if price:
            body['price'] = str(price)

        if stop_price:
            body['stop-price'] = str(stop_price)

        if operator:
            body['operator'] = operator

        sign_data = self._sign('POST', path)

        url = self.host + path + '?' + self._build_params(sign_data)
        print(url)
        print(json.dumps(sign_data))  # ''
        # exit()

        headers = {"Content-Type": "application/json"}
        json_data = requests.post(url, headers=headers, data=json.dumps(body), timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']
        raise Exception(f"请求{url}发生错误...{json_data}")

        # return self._request(RequestMethod.POST, path, body=body, verify=True)

    def cancel_order(self, order_id):
        path = f'/v1/order/orders/{order_id}/submitcancel'

        url = self.host + path
        sign_data = self._sign('POST', path)
        url += '?' + self._build_params(sign_data)
        headers = {"Content-Type": "application/json"}
        json_data = requests.post(url, headers=headers, timeout=self.timeout).json()
        print(json_data)
        if json_data['status'] == 'ok':
            return json_data['data']
        else:
            return json_data

        # return self._request(RequestMethod.POST, path, verify=True)

    def get_open_orders(self, account_id, symbol, side=None, from_=None, direct=None, size=100):
        """

        :param account_id:
        :param symbol:
        :param side:
        :param from_: 查询起始 ID
        :param direct: 如字段'from'已设定，此字段'direct'为必填) 查询方向 (prev - 以起始ID升序检索；next - 以起始ID降序检索)
        :param size:
        :return:
        """

        path = '/v1/order/openOrders'
        params = {'account-id': account_id,
                  "symbol": symbol,
                  "size": size}
        if side:
            params["side"] = side

        if from_ and direct:
            params['from'] = from_
            params['direct'] = direct


        sign_data = self._sign('GET', path, params=params)

        url = self.host + path + '?' + self._build_params(sign_data)
        # print(url)
        # exit()
        json_data = requests.get(url, timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']
        raise Exception(f'请求{url}发生错误..{json_data}')

        # return self._request(RequestMethod.GET, path, params=params, verify=True)



    def cancel_orders(self, account_id, symbol=None, side=None, size=None):
        path = "/v1/order/orders/batchCancelOpenOrders"

        body = {'account-id': account_id}

        if symbol:
            body['symbol'] = symbol

        if side:
            body['side'] = side

        if size:
            body['size'] = size

        url = self.host + path

        sign_data = self._sign('POST', path)
        url += '?' + self._build_params(sign_data)
        headers = {"Content-Type": "application/json"}
        json_data = requests.post(url, headers=headers, data=json.dumps(body), timeout=self.timeout).json()
        if json_data['status'] == 'ok':
            return json_data['data']
        else:
            return json_data
        raise Exception(f"请求{url}的数据发生错误, 错误信息--> {json_data}")

        # return self._request(RequestMethod.POST, path, body=body, verify=True)

    def cancel_orders_by_ids(self, ids:list):
        path = '/v1/order/orders/batchcancel'
        body = {'order-ids': ids}

        url = self.host + path
        sign_data = self._sign('POST', path)
        url += '?' + self._build_params(sign_data)
        headers = {"Content-Type": "application/json"}
        json_data = requests.post(url, headers=headers, data=json.dumps(body), timeout=self.timeout).json()
        print(json_data)
        if json_data['status'] == 'ok':
            return json_data['data']
        else:
            return json_data

        # return self._request(RequestMethod.POST, path, body=body, verify=True)

    def get_order_details(self, order_id):
        path = f'/v1/order/orders/{order_id}'

        sign_data = self._sign('GET', path)
        url = self.host + path + '?' + self._build_params(sign_data)

        json_data = requests.get(url, timeout=self.timeout).json()
        print(json_data)
        if json_data['status'] == 'ok':
            return json_data['data']

        raise Exception(f'请求{url}发生错误..{json_data}')

        # return self._request(RequestMethod.GET, path, verify=True)


if __name__ == '__main__':

    key = "xxx"
    secret = "xxx"
    huobi = HuobiHttpClient(key=key, secret=secret)

    # data = huobi.get_symbols()
    # print(data)
    # data = huobi.get_currencys()
    # print(data)

    # data = huobi.get_time_stamp()
    # print(data)
    #
    # print(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    while True:
        data = huobi.get_kline_data("btcusdt", HuobiPeriod.MINUTE_1, size=200)
        df = pd.DataFrame(data, columns={"id": 0, 'vol': 1, 'count': 2, 'open': 3, 'close': 4, 'low': 5,
                                                   'high': 6, 'amount': 7})
        df = df[['id', 'open', 'high', 'low', 'close', 'amount']]
        df = df.iloc[::-1]
        df["conversion_min"] = talib.MIN(df["low"], 9)
        df["conversion_max"] = talib.MAX(df["high"], 9)
        df["conversion"] = (df["conversion_min"] + df["conversion_max"]) / 2
        df["base_min"] = talib.MIN(df["low"], 26)
        df["base_max"] = talib.MAX(df["high"], 26)
        df["base"] = (df["base_min"] + df["base_max"]) / 2
        df["leada"] = (df["conversion"] + df["base"]) / 2
        df["leadb_min"] = talib.MIN(df["low"], 52)
        df["leadb_max"] = talib.MAX(df["high"], 52)
        df["leadb"] = (df["leadb_min"] + df["leadb_max"]) / 2
        df = df[['id', 'open', 'high', 'low', 'close', 'amount', 'conversion', 'base', 'leada', 'leadb']]
        print(df)
        time.sleep(10)


    # data = huobi.get_tickers()
    # print(data)

    # data = huobi.get_accounts()
    # print(data)


    # balance = huobi.get_account_balance('897261')
    # print(balance)

    # order_id = huobi.place_order('897261', 'btcusdt', 'buy-limit', '0.01', '7500')
    # print(order_id)


    # order_id = huobi.place_order('897261', 'btcusdt', 'buy-limit', '0.01', '7500')
    # print(order_id)
    # exit()
    # import time
    # time.sleep(3)
    # order_id = '50813087667'
    # huobi.cancel_order(order_id)

    # orders = huobi.get_open_orders('897261', 'btcusdt')
    # print(orders)

    # data = huobi.cancel_orders('897261')
    # print(data)


    # data = huobi.cancel_orders_by_ids(['50814410681'])
    # print(data)


    # order_detail = huobi.get_order_details('50814441441')
    # print(order_detail)