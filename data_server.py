from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import multiprocessing
import time
import data_read
import json

def read_length(data_length):
    return 5+2*data_length

def byte_reverser(byte):
    return ((byte&0x80)>>7)+((byte&0x40)>>5)+((byte&0x20)>>3)+((byte&0x10)>>1)+((byte&0x08) <<1)+((byte&0x04)<<3)+((byte&0x02)<<5)+((byte&0x01)<<7) 

def dreflect(dic):
	return {v:k for k,v in dic.items()}

class gateway_without_buffer(data_read.gateway_interface):
    def __init__(self,port,baud):
        print('creating')
        super().__init__(port,baud)

    def read_device__(self,dev_offset):
        data_start=132
        raw=self.read_bytes(132+dev_offset*7,7)
        #print(raw)
        data=[]
        for i in range(0,len(raw)) :
            if i < 8:
                if i in [0,2,4,6]:
                    data.append(raw[i])
                else:
                    data[-1]=(data[-1]<<8)+raw[i]
            else:
                data=data+[raw[i]]
        return data

    def read_device_raw(self,dev_offset):
        data = self.read_device__(dev_offset)
        res = {self.dev_reg_description[i]:data[i] for i in range(0,len(data))}
        return res

    def read_device_adj(self,dev_offset):
        res=self.read_device_raw(dev_offset)
        for i in ['sensor0','sensor1','sensor2','sensor3']:
            print(res[i] &0x3000)
            if (res[i] &0x3000) != 0:
                res[i] = 'err'
            elif res[i] == 0x8000:
                res[i] = 'masked'
            else:
                res[i]= res[i] & 0x03ff
        return res

    def uuid2offset(self,uuid):
        return self.dev_map[uuid]

    def offset2uuid(self,offset):
        return dreflect(self.dev_map)[offset]
    
    def mute(self):
        return self.write_reg(580,0)

    def read_all(self):
        return  { "%#06X" % i :self.read_device_adj(i) for i in self.dev_offset }

    def alert(self):
        raw=[self.read_device_raw(i) for i in self.dev_offset]
        seprated=[ [ ((i[k]&0xcff ) >> 8)>2  for k in ['sensor0','sensor1','sensor2','sensor3'] ] for i in raw  ]
        print(seprated)
        return {"%#06X" % self.dev_offset[i]:{'sensor'+str(j) :{  'alert':seprated[i][j] } for j in range(0,len(seprated[i]))   } for i in range(0,len(self.dev_uuid))}
    
    def full_data(self):
        raw={"%#06X" % i :self.read_device_raw(i) for i in self.dev_offset}
        for i in self.dev_offset:
            raw["%#06X" % i ]['uuid']=  "%#08X" %  self.offset2uuid(i) 
            raw["%#06X" %  i]['alert']= {   j: ((raw["%#06X" %  i][j]&0xcff) >>8)>>2  for j in ['sensor'+str(k)  for k in range(0,4)]}
            print( str(int(raw["%#06X" %  i]['uuid'],base=0))[-7:-4] )
            if  str(int(raw["%#06X" %  i]['uuid'],base=0))[-7:-4]  == '127' :
                raw["%#06X" %  i]['type']='portable'
            else:
                raw["%#06X" %  i]['type']='fixed' 
            for k in ['sensor0','sensor1','sensor2','sensor3']:
               # print(raw["%#06X" %  i][k] &0x3000)
                if (raw["%#06X" %  i][k] &0x3000) != 0:
                    raw["%#06X" %  i][k] = 'err'
                elif raw["%#06X" %  i][k] == 0x8000:
                    raw["%#06X" %  i][k] = 'masked'
                else:
                    raw["%#06X" %  i][k]= raw["%#06X" %  i][k] & 0x03ff
        return raw

        
       
        


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
        path_l=[ i for i in path_l if i != '']
        print(path_l)
        if path_l[0] == 'gateway':
            try:
                gateway[0].is_exist()
            except AttributeError:
                self.send_error(404,'Not Found')
            else:
                if len(path_l) == 1:
                    self.__send_json({"gateway":gateway[0].read_all() })

                elif len(path_l) == 2:
                    flg = 0
                    try:
                        int(path_l[-1],base=0)
                    except ValueError:

                        if path_l[-1] == "list_devices" :
                            self.__send_json({ 'devices':  str([ "%#06X" % a  for a in gateway[0].dev_offset]) })
                        elif path_l[-1] == 'details':
                            self.__send_json(gateway[0].full_data() )
                        elif path_l[-1] == 'list_device_uuid'  :
                            self.__send_json({ 'uuid':  str([ "%#010" % a  for a in gateway[0].dev_uuid]) })
                        
                        elif path_l[-1] == 'alert':
                            self.__send_json(gateway[0].alert()) 
                        
                        elif path_l[-1] == 'mute':
                            res=gateway[0].mute()
                            print(res)
                            if res == 0:
                                self.__send_json({'success':1})
                            else:
                                self.send_error(500,'Internal Server Error')
                        else:
                            self.send_error(400,'Bad Request')
                    else:
                        if len(path_l[-1])>7 :
                            if int(path_l[-1],base=0) in gateway[0].dev_uuid:
                                self.__send_json(gateway[0].read_device_adj(gateway[0].dev_map[int(path_l[-1],base=0)]))

                            else:
                                self.send_error(400,'Bad Request')
 
                        elif int(path_l[-1],base=0) in gateway[0].dev_offset :
                            self.__send_json(gateway[0].read_device_adj(int(path_l[-1],base=0)))

                        else :
                            self.send_error(500,'Internal Server Error')

            if len(path_l) == 3 :
                try:
                    dev=int(path_l[-2],base0)
                except ValueError:
                    self.send_error(400,'Bad Request')              
                else:
                    if len(path_l[-2])<8:
                        if dev in gateway[0].dev_offset:
                            if path_l[-1] in gateway[0].dev_reg_description:
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
        if   'application/json' not in self.headers.get('Content-Type',''):
            self.send_error(400,'Bad Request')

        if self.path == '/gateway/setting':
            body=self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8')
            req=eval(body)
            print(req)
            gateway[0]=gateway_without_buffer(req['port'],req['baud'])
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