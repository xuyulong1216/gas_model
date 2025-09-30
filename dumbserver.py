from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
#from mulitiprocessing.managers import Manager,Process
import time
import json
class dumb_atmo:
    def __init__(self,port,baud):
        self.port=port
        self.addr=1
        self.baud=baud
        self.sensors=['wind_speed','wind_power','wind_direction_analog','wind_direction_degree','temperature','humidit','noise','variable','PM10','air_pressure','illuminance','rainfall','compass','sun_radient']
        self.addrs=[[500],[501],[502],[503],[504],[505],[506],[507],[508],[509],[510,511],[512],[513],[514],[515]]
        self.compat={self.sensors[i]:self.addrs[i] for i in range(0,len(self.addrs))}
			
    def read(self,sensor):
        res=0xba
        for i in range(0, 2*len(self.compat[sensor])):
            res = (res << 8) + 0xba
        return res

    def read_all(self):
        return { k:self.read(k) for k in self.sensors}

class dumb_gateway:
    def __init__(self,port,baud):
        self.port=port
        self.addr=1
        self.chn=17-self.addr
        self.baud=baud
		#self.ser=serial.Serial(port,baud,timeout=1)
        self.sensors=[i for i in range(1,0x15)]
			
    def read(self,start_addr,data_length):
        res=0xab
        for i in range(0,data_length):
            res = (res << 8) + 0xAB
        return res

    def read_all(self):
        return {"%#04X" %  k:self.read(k,2) for k in self.sensors}

class dumb_predictor:
    def __init__(self):
        self.gas_sensors={'CO':[0X01,0X04,0X07,0X0A],'H2S':[0x02,0x05,0x08,0x0B],'flammable':[0x03,0x06,0x09,0x0c] }

    def predict(self,gas_type,coords):
        return sum(coords)

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path_l=self.path.split('/')
        del(path_l[0])
        print(path_l)
        if path_l[0] == 'gateway':
            if len(path_l) == 1:
                try:
                    data=gateway[0].read_all()
                except AttributeError:
                    self.send_error(404,'Not Found')
                else: 
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write((json.dumps(data)+ '\n').encode('utf-8'))
            elif len(path_l) == 2:
                try:
                    data=gateway[0].read(int(path_l[-1],base=0),2)
                except AttributeError:
                    self.send_error(404,'Not Found')
                else :
                    if int(path_l[-1],base=0) in gateway[0].sensors :
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write((json.dumps({ "%#04X" % int(path_l[-1],base=0) :data})+ '\n').encode('utf-8'))
            else:
                self.send_error(400,'Bad Request')

        if path_l[0] == 'atmosphere':
            if len(path_l) == 1:
                try:
                    data=atmo_meter[0].read_all()
                except AttributeError:
                    self.send_error(404,'Not Found')
                else: 
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write((json.dumps(data)+ '\n').encode('utf-8'))
            elif len(path_l) == 2:
                try:
                    data=atmo_meter[0].read(path_l[-1])
                except AttributeError:
                    self.send_error(404,'Not Found')
                else:
                    if int(path_l[-1]) in atmo_meter[0].sensors :
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write((json.dumps({ path_l[-1] :data})+ '\n').encode('utf-8'))
                    elifif path_l[-1] == 'list_sensors':
                     self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write((json.dumps({'sensors':str(atmo_meter[0].sensors)})+ '\n').encode('utf-8'))
                    else:
                        self.send_error(400,'Bad Request')
            else:
                self.send_error(400,'Bad Request')

        elif path_l[0] == 'predictor':
            flg=0
            try:
                data=read_all(gateway[0])
            except AttributeError:
                self.send_error(404,'Not Found')
                flg=1
              
            if (len(path_l) == 1 or len(path_l) == 2 )and flg==0:
                self.send_error(400,'Bad Request')
            elif (len(path_l) == 3 ) and flg==0 :
                if path_l[1] not in list(predictor.gas_sensors.keys()):
                    self.send_error(400,'Bad Request')
                else:
                    coords=path_l[-1].split('_')
                    #print(coords)
                    if len(coords) != 4  :
                        self.send_error(400,'Bad Request')
                    else :
                        for i in range(0,len(coords)) :
                            if  ('e' in coords[i] )or ('E' in coords[i]) :
                                flg = 1
                            try:
                                coords[i]=float(coords[i])
                            except ValueError:
                                flg = 1
                    if flg == 0 :
                        response=json.dumps( {path_l[-1] : predictor.predict(path_l[1],coords) } ) + '\n'
                        time.sleep(0.3)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(response.encode('utf-8'))
                    else:
                        self.send_error(400,'Bad Request')
            
        else:
            self.send_error(400,'Bad Request')
    def do_POST(self):
        path_l=self.path.split('/')
        del(path_l[0])

        if self.path not in ['/gateway/setting','/atmosphere/setting']or  'application/json' not in self.headers.get('Content-Type',''):
            self.send_error(400,'Bad Request')
        elif path_l[0] == 'gateway':
            req=eval(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
            
            gateway[0]=dumb_gateway(req['port'],req['baud'])
            self.send_error(201,'Created')
        elif path_l[0] == 'atmosphere':
            req=eval(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
            
            atm_meter[0]=dumb_atmo(req['port'],req['baud'])
            self.send_error(201,'Created')

if __name__ == '__main__':
    gateway=[1]
    atm_meter=[1]
    server_address = ('', 8000)
    predictor=dumb_predictor()
    #manager=Manager()
    #dict_shared=manager.dict()
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server...')
    httpd.serve_forever()
