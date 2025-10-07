import  pymodbus
import serial as ser
import multiprocessing as mp

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


class gateway_reader:
    def __init__(self,port,baud):
        self.port=port
        self.addr=1
        self.baud=baud
        self.ser=ser.Serial(port,baud,timeout=1)
        self.reg_distribution=[[0],[1],[2],[3],[4,131],[132,579],[580],[581],[582,589],[590,597],[598,599],[600],[601,616],[617,624],[625,632],[633],[634],[635]]
        for i in range (1,18):
            read=[i,0x03,0x00,0x01,0x00,0x01]
            self.ser.write(bytearray(addcrc(command)))
            result=self.ser.readline()
            if len(result) != 0 and list(result) != [0x05,0xc8,0x01,0xf1,0xc1]:
                self.addr=i
                break

    def read(self,start_addr,data_length):
        start_addr=((start_addr & 0xff00 )>>8),(start_addr& 0x00ff)
        data_length=((data_length & 0xff00) >>8),(data_length & 0x00ff)
        command=[self.addr,0x03,*start_addr,*data_length]
        self.ser.write(bytearray(addcrc(command)))
        re=list(self.read(3))
        re=re+list(self.ser.read(re[-1]+2))
        return [(re[3+2*i]<<8)+re[2*i+4] for i in range(0,(re[2])//2)]
    
    def read_all_regs(self):
        regs=[]
        for i in range (0,635,125):
            if 635-i-125 <0:
                k=10
            else:
                k=125
            regs=regs+self.read(i,k)
        return regs

    def read_group(self,group_num):
        regs=[]
        reg_start=self.reg_distribution[group_num][0]
        reg_end=self.reg_distribution[group_num][-1]
        for i in range (reg_start,reg_end+1,125):
            if reg_end-i-125 <0:
                k=reg_end-i
            else:
                k=125
            regs=regs+self.read(i,k)
        return regs

        
    

    