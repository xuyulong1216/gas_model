from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import multiprocessing
import time
import data_read

def read_length(data_length):
    return 5+2*data_length

def byte_reverser(byte):
    return ((byte&0x80)>>7)+((byte&0x40)>>5)+((byte&0x20)>>3)+((byte&0x10)>>1)+((byte&0x08) <<1)+((byte&0x04)<<3)+((byte&0x02)<<5)+((byte&0x01)<<7) 

def dreflect(dic):
	return {v:k for k,v in dic.items()}

class gateway_with_buffer(data_read.gateway_interface):
    def __init__(self,port,baud):
        super().__init__(port,baud)

    def alert(self):
        raw=[self.read_device(i) for i in self.dev_offset]
        seprated=[ [[(i[k]&0xf0)>>4,i[k]&0xf]  for k in ['stat0','stat1','stat2','stat3'] ] for i in raw  ]
        return {self.dev_uuid[i]:{'sensor'+str(j) :{  'alert':k[-1] if k[0]== 0xa,'error' :k[-1] if k[0]==0xb for k in seprated[i][j] } for j in range(0,len(seprated[i]))} for i in range(0,len(self.dev_uuid))}
    
    def uuid2offset(self,uuid):
        return self.dev_map[uuid]
    
    def diaslert(self):
        self.write_reg(580,0)

    
class dumb_predictor:
    def __init__(self):
        self.gas_sensors={'CO':[0X01,0X04,0X07,0X0A],'H2S':[0x02,0x05,0x08,0x0B],'flammable':[0x03,0x06,0x09,0x0c] }
    def predict(self,gas_type,coords):
        return sum(coords)

class MyHandler(BaseHTTPRequestHandler):

    def __send_json(self,dic):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write((json.dumps(dic)+ '\n').encode('utf-8'))
        
    def do_GET(self):
        path_l=self.path.split('/')
        del(path_l[0])
        print(path_l)
        '''
        for i in path_l:
            
            
            '''
        if path_l[0] == 'gateway':
            try:
                gateway[0].is_exist()
            except AttributeError:
                self.send_error(404,'Not Found')

            else:
                if len(path_l) == 1:
                    self.__send_json(self,gateway[0].read_all())

                elif len(path_l) == 2:
                    flg=0

                    if len(path_l[-1]>8):
                        if path_l[-1] in gateway[0].dev_uuid :
                            self.__send_json(gateway[0].read_device(gateway[0].dev_map[path_l[-1]]))
                        else:
                            self.send_error(500,'Internal Server Error')

                    elif int(path_l[-1],base=0) in gateway[0].dev_offset  and flg == 0:
                        self.__send_json{gateway[0].read_device(int(path_l[-1],base=0))}  

                    elif path_l[-1] == "list_devices" and flg==0 :
                        self.__send_json({ 'devices':  str([ "%#06X" % a  for a in gateway[0].dev_offset]) })
                    
                    elif path_l[-1] == 'list_device_uuid' and flg == 0 :
                        self.__send_json({ 'uuid':  str([ "%#08X" % a  for a in gateway[0].dev_uuid]) })
                    
                    elif path_l[-1] == 'alert' and flg==0:
                        self.__send_json(gateway[0].alert())

                    else :
                        self.send_error(500,'Internal Server Error')

                elif len(path_l) == 3 :
                    if len(path_l[-2])<8:
                        if int(path_l[-2],base=0) in gateway[0].dev_offset:
                            if path_l[-1] in gateway[0].dev_reg_description:path_l[-1]
                                self.__send_json({path_l[-1] :gateway[0].read_device(int(path_l[-2],base=0)[path_l[-1]] )} )
                            else:
                                self.send_error(500,'Internal Server Error')
                        elif path_l[-2] in gateway[0].dev_uuid :
                            self.__send_json({path_l[-1]:gateway[0].read_device(gateway[0].dev_map[path_l[-2]])[path_l[-1]]})
                                
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
            
        elif path_l[-1] == 'alert' and len(path_l[-1]) == 1 :
            return gateway[0].alert()
        

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
            
            gateway[0]=gateway_with_buffer(req['port'],req['baud'])
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