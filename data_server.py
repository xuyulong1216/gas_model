from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)  # 解析请求路径
        query_params = parse_qs(parsed_path.query)  # 解析查询参数，返回一个字典，值是列表形式

        # 获取特定参数的值，例如 'name'
        name = query_params.get('name', ['未知'])[0]  # 如果没有提供 name 参数，默认为 '未知'

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        response_message = f"你好, {name}! 你访问的路径是: {parsed_path.path}".encode('utf-8')
        self.wfile.write(response_message)
if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server...')
    httpd.serve_forever()