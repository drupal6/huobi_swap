from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from utils import logger
from utils.dingding import DingTalk


strategy = None


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # print(self.headers)
        # print(self.command)
        req_datas = self.rfile.read(int(self.headers['content-length']))
        req_data = json.loads(req_datas.decode())
        req_param = req_data["text"]["content"].rstrip()

        if strategy:
            msg = None
            if req_param == "h":
                msg = strategy.e_g()
            elif req_param == "s":
                msg = strategy.show()
            else:
                if "=" in req_param:
                    params = req_param.split("=")
                    key = params[0]
                    value = params[1]
                    msg = strategy.set_param(key, value)
                    if not msg:
                        msg = "not support. %s" % req_param
                else:
                    msg = "param error. %s" % req_param
            if msg:
                DingTalk.send_text_msg(content= "\n" + msg)


class MyHttpServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        try:
            http_server = HTTPServer(('', int(self.port)), HTTPHandler)
            http_server.serve_forever()
        except BaseException:
            logger.error("MyHttpServer error.", caller=self)


if __name__ == "__main__":
    ms = MyHttpServer(8080)
    ms.start()




