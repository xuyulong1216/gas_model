import  pymodbus
import serial as ser
chn_addr={}

def crc(bytes):
    preset=0xffff
    for b in bytes:
        preset^=b
        for i in range(8):
            if preset & 0x0001:
                preset=(preset>>1) ^ 0xa001
            else:
                preset>>=1

    return (preset & 0x00ff),((preset & 0xff00) >>8)

def addcrc(command):
    return command+[*crc(bytearray(command))]



class gateway:
    def __init__(self,port,baud):
        self.port=port
        self.addr=addr
        self.chn=17-addr
        self.baud=baud
        self.ser=serial.Serial(port,baud,timeout=1)
        self.sensors=[]
        for i in range (1,18):
            read=[i,0x03,0x00,0x01,0x00,0x01]
            self.ser.write(bytearray(addcrc(command)))
            result=self.ser.read(self.ser.in_waiting)
            if len(result) != 0 and result != [0x05,0xc8,0x01,0xf1,0xc1]:
                self.addr=i
                break
            
    def read(self,start_addr,data_length):
        start_addr=(start_addr & 0xff00 >>8),(start_addr& 0x00ff)
        data_length=(data_length & 0xff00 >>8),(data_length & 0x00ff)
        command=[self.addr,0x03,*start_addr,*data_length]
        self.ser.write(bytearray(addcrc(command)))
        re=list(self.ser.read(self.ser.in_waiting))
        return [re[i]<<8+re[i+1] for i in range(3,len(re-2)/2)]
    
    def read_all(self):
        pass


    