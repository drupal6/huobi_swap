import requests
from enum import Enum
from threading import Thread, Lock


class RequestMethod(Enum):
    """
    请求的方法.
    """
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

class HuobiFutureHttp(object):

    def __init__(self, key=None, secret=None, host=None, timeout=5):
        self.key = key
        self.secret = secret
        self.host = host if host else "https://api.huobi.pro"
        self.recv_window = 5000
        self.timeout = timeout
        self.order_count_lock = Lock()
        self.order_count = 1_000_000

    def build_parameters(self, params: dict):
        keys = list(params.keys())
        keys.sort()
        return '&'.join([f"{key}={params[key]}" for key in params.keys()])

    def request(self, req_method: RequestMethod, path: str, requery_dict=None, verify=False):
        url = self.host + path

        if verify:
            query_str = self._sign(requery_dict)
            url += '?' + query_str
        elif requery_dict:
            url += '?' + self.build_parameters(requery_dict)
        # print(url)
        headers = {"X-MBX-APIKEY": self.key}

        return requests.request(req_method.value, url=url, headers=headers, timeout=self.timeout).json()

    def get_kline(self, symbol, interval, limit=500, max_try_time=10):
        """

        :param symbol:
        :param interval:
        :param start_time:
        :param end_time:
        :param limit:
        :return:
        [
            1499040000000,      // 开盘时间
            "0.01634790",       // 开盘价
            "0.80000000",       // 最高价
            "0.01575800",       // 最低价
            "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
            "148976.11427815",  // 成交量
            1499644799999,      // 收盘时间
            "2434.19055334",    // 成交额
            308,                // 成交笔数
            "1756.87402397",    // 主动买入成交量
            "28.46694368",      // 主动买入成交额
            "17928899.62484339" // 请忽略该参数
        ]
        """
        path = "/market/history/kline"

        query_dict = {
            "symbol": symbol,
            "period": interval,
            "size": limit
        }

        for i in range(max_try_time):
            data = self.request(RequestMethod.GET, path, query_dict)
            if isinstance(data, list) and len(data):
                return data


if __name__ == '__main__':

    key = "xxx"
    secret = 'xxx'
    huobi = HuobiFutureHttp(key=key, secret=secret)

    data = huobi.get_kline('btcusdt', "1min", limit=200)
    print(data)
    print(isinstance(data, list))
