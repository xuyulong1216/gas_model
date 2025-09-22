from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import data_read
import model

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 GET 请求"""
        path_l=self.path.split('/')
        if path_l[0] == 'gateway':
            if len(path_l) == 1:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(str(read_all()).encode('utf-8'))
            if len(path_l) == 2:
                if int(path_l[-1]) in data_read.gateway.sensors :
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(str({path_l[-1]:data_read.gateway.read(int(path_l),2)}).encode('utf-8'))
            
        elif path_l[0] == 'predictor':
            if len(path_l) == 1:
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
            elif len(path_l) == 2 :
                coords=path_l[-1].split(@):
                    if len(coords) != 4 :
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        elf.end_headers()
                    else :
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(str({path_l[-1]:}).encode('utf-8'))

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write("这是关于我们.".encode('utf-8'))
        else:
            # 处理不存在的路径
            self.send_error(404, "页面未找到")
def read_all:
    return {k,data_read.gateway.read(k,2) for k in data_read.gateway.sensors}

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server...')
    httpd.serve_forever()