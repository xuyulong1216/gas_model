from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import multiprocessing
import time
import data_reader

def read_length(data_length):
    return 5+2*data_length

def byte_reverser(byte):
    return ((byte&0x80)>>7)+((byte&0x40)>>5)+((byte&0x20)>>3)+((byte&0x10)>>1)+((byte&0x08) <<1)+((byte&0x04)<<3)+((byte&0x02)<<5)+((byte&0x01)<<7) 

class gateway:
    def __init__(self,port,baud):
        self.reader=data_reader.gateway_reader(port,baud)
        bitmap=0
        for i in range(0,4):
            bitmap=(bitmap<<16)+(byte_reverser((self.reader.read_group(i)[0]&0xff00 )>>8)<<8)+byte_reverser(self.reader.read_group(i)[0]&0xff)
        self.dev_reg_description=['sensor0','sensor1','sensor2','sensor3','dev_bat_H','dev_bat_L','stat0','stat1','stat2','stat3']
        self.dev_offset=[]
        for i in range(0,64):
            if (0x8000 0000 0000 0000 >>i )& bitmap !=0:
                self.dev_offset.append(i)

    def is_exist(self):
        return 1
        
    def read_device(self,dev_offset):
        data_start=132
        raw=self.reader.read(132+dev_offset,14)
        raw=[raw[i] for i in range(0,4) ]+[*((raw[i]&0xff00>>8),raw[i]&0xff) for i in range(4,len(raw)) ]
        return { self.dev_reg_description[i]:raw[i] for i in range(0,len(data))}
    
    
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
            try:
                gateway[0].is_exist()
            except AttributeError:
                self.send_error(404,'Not Found')
            else:
                if len(path_l) == 1:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write((json.dumps()+ '\n').encode('utf-8'))

                elif len(path_l) == 2:
                    if int(path_l[-1],base=0) in gateway[0].dev_offset :
                        data=gateway[0].read_device()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write((json.dumps(data)+ '\n').encode('utf-8'))

                    elif path_l[-1] == "list_devices" :
                        self.send_response(200)
                        self.send_header('Content-type','application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({ 'devices':  str([ "%#06X" % a  for a in gateway[0].dev_offset]) } ) )
                    
                    else :
                        self.send_error(500,'Internal Server Error')

                elif len(path_l) == 3 :
                    if int(path_l[-2],base=0) in gateway[0].dev_offset:
                        if path_l[-1] in gateway[0].dev_reg_description:
                            data=gateway
                            self.send_response(200)
                            self.send_header('Content-type','application/json')
                            self.end_headers()
                            self.wfile.erite(json.dumps({}))
                        
                else:
                    self.send_error(400,'Bad Request')

        elif path_l[0] == 'atmosphere':
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
                    data=atmo_meter[0].is_exist()
                except AttributeError:
                    self.send_error(404,'Not Found')
                else:
                    if path_l[-1] in atmo_meter[0].sensors :
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        data=data=atmo_meter[0].read(path_l[-1])
                        self.wfile.write((json.dumps({ path_l[-1] :data})+ '\n').encode('utf-8'))
                    elif path_l[-1] == 'list_sensors':
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
        print(self.path)
        if self.path not in ['/gateway/setting','/atmosphere/setting'] or  'application/json' not in self.headers.get('Content-Type',''):
            self.send_error(400,'Bad Request')
        elif path_l[0] == 'gateway':
            req=eval(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
            
            gateway[0]=dumb_gateway(req['port'],req['baud'])
            self.send_error(201,'Created')
        elif path_l[0] == 'atmosphere':
            req=eval(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
            
            atmo_meter[0]=dumb_atmo(req['port'],req['baud'])
            self.send_error(201,'Created')

if __name__ == '__main__':
    gateway=[1]
    atmo_meter=[1]
    server_address = ('', 8000)
    predictor=dumb_predictor()
    #manager=Manager()
    #dict_shared=manager.dict()
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server...')
    httpd.serve_forever()