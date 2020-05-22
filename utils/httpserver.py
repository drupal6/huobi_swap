from socket import *
from select import select


class HTTPServer:
    """
    将具体http server功能封装
    """

    def __init__(self, server_address):
        self.server_address = server_address
        self.rlist = self.wlist = self.xlist = []
        self.create_socket()
        self.bind()

    def create_socket(self):
        """
        创建套接字
        :return:
        """
        self.sockfd = socket()
        self.sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def bind(self):
        self.sockfd.bind(self.server_address)
        self.ip = self.server_address[0]
        self.port = self.server_address[1]

    def serve_forever(self):
        """
        启动服务
        :return:
        """
        self.sockfd.listen(5)
        print("Listen the port %d" %self.port)
        self.rlist = [self.sockfd]
        self.wlist = []
        self.xlist = []
        while True:
            rs, ws, xs = select(self.rlist, self.wlist, self.xlist)
            for r in rs:
                if r is self.sockfd:
                    c, addr = r.accept()
                    print('Connect from', addr)
                    self.rlist.append(c)
                else:
                    # 处理浏览器
                    self.handle(r)

    # 处理客户端请求
    def handle(self, connfd):
        # 接收http请求
        request = connfd.recv(1024)
        # 防止浏览器断开
        if not request:
            self.rlist.remove(connfd)
            connfd.close()
            return

        # 请求解析
        request_line = request.splitlines()[0]
        info = request_line.decode().split(' ')[1]
        print(connfd.getpeername(), ':', info)

    def do_POST(self):
        print(self.headers)
        print(self.command)
        req_datas = self.rfile.read(int(self.headers['content-length']))  # 重点在此步!
        print(req_datas.decode())
        data = {
            'result_code': '2',
            'result_desc': 'Success',
            'timestamp': '',
            'data': {'message_id': '25d55ad283aa400af464c76d713c07ad'}
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


if __name__ == '__main__':
    server_addr = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_addr)
    httpd.serve_forever()
