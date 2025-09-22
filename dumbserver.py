from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class dumb_gateway:
	def __init__(self,port,baud):
		self.port=port
		self.addr=1
		self.chn=17-addr
		self.baud=baud
		#self.ser=serial.Serial(port,baud,timeout=1)
		self.sensors=[i for i in range(1,0x15)]

		'''for i in range (1,18):
			read=[i,0x03,0x00,0x01,0x00,0x01]
			self.ser.write(bytearray(addcrc(command)))
			result=self.ser.read(self.ser.in_waiting)
			if len(result) != 0:
				self.addr=i
				break'''
			
	def read(start_addr,data_length):
		res=0
        for i in range(0,data_length):
            res=res <<8 +0xab
        return res

def read_all(gateway):
    return {k,gateway.read(k,2) for k in gateway.sensors}


class dumb_predictor:
    def __init__(self):
        self.gas_sensors={'CO':[0X01,0X04,0X07,0X0A],'H2S':[0x02,0x05,0x08,0x0B],'flammable':[0x03,0x06,0x09,0x0c] }
    def predict(gas_type,coords):
        return sum(coords)

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path_l=self.path.split('/')
        if path_l[0] == 'gateway':
            if len(path_l) == 1:
                try:
                    data=read_all(gateway):
                except NameError:
                    self.send_error(404,'Not Found')
                else: 
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data.encode('utf-8'))
            if len(path_l) == 2:
                try:
                    data=gateway.read(int(path_l),2):
                except NameError:
                    self.send_error(404,'Not Found')
                else:
                    if int(path_l[-1]) in gateway.sensors :
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(str({path_l[-1]:data}).encode('utf-8'))
            else:
                self.send_error(400,'Bad Request')
            
        elif path_l[0] == 'predictor':

            if len(path_l) == 1 or len(path_l) == 2:
                self.send_error(400,'Bad Request')
            elif len(path_l) == 3 :
                if path_l[1] not in list(predioctor.gas_sensors.keys()):
                    self.send_error(400,'Bad Request')
                else:
                    coords=path_l[-1].split('@')
                    if len(coords) != 4 :
                        self.send_error(400,'Bad Request')
                    else :
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(str({path_l[-1]:predictor(path_l[1],[int(i)for i in coords])}).encode('utf-8'))
        else:
            self.send_error(400,'Bad Request')
    def do_POST(self):
        if self.path != '/gateway/setting' or  'application/json' not in self.headers.get('Content-Type',''):
            self.send_error(400,'Bad Request')
        else:
            gateway=dumb_gateway(dict(self.rfile.read(int(self.headers.get('Content-Length', 0)))))['port'],dict(self.rfile.read(int(self.headers.get('Content-Length', 0)))['baud'])
            self.send_response(201)

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server...')
    httpd.serve_forever()