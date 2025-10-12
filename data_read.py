
import serial as ser

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

def byte_reverser(byte):
    return ((byte&0x80)>>7)+((byte&0x40)>>5)+((byte&0x20)>>3)+((byte&0x10)>>1)+((byte&0x08) <<1)+((byte&0x04)<<3)+((byte&0x02)<<5)+((byte&0x01)<<7)

class gateway_interface:
    def __init__(self,port,baud):
        self.port=port
        self.addr=1
        self.baud=baud
        self.ser=ser.Serial(port,baud,timeout=1)
        self.reg_distribution=[[0],[1],[2],[3],[4,131],[132,579],[580],[581],[582,589],[590,597],[598,599],[600],[601,616],[617,624],[625,632],[633],[634],[635]]

        for i in range (1,18):
            read=[i,0x03,0x00,0x01,0x00,0x01]
            self.ser.write(bytearray(addcrc(read)))
            result=self.ser.readline()
            if len(result) != 0 and list(result) != [0x05,0xc8,0x01,0xf1,0xc1]:
                self.addr=i
                break

        self.bitmap=0
        for i in range(0,4):
            tmp=self.read_group(i)
            self.bitmap=(self.bitmap<<16)+( (byte_reverser((tmp[0]&0xff00 )>>8)<<8)+byte_reverser(tmp[0]&0xff) )
        
        self.dev_offset=[ i for i in range(0,64) if ((self.read(4+i*2,2)[0]<<8)+self.read(4+i*2,2)[-1] )  !=0  and i<20 ]
        self.dev_uuid=[ (self.read(4+i*2,2)[0]<<8)+self.read(4+i*2,2)[-1] for i in self.dev_offset]
        self.dev_map={self.dev_uuid[i]:self.dev_offset[i]  for i in range(0,len(self.dev_offset))}
        self.dev_reg_description=['sensor0','sensor1','sensor2','sensor3','dev_bat_H','dev_bat_L','stat0','stat1','stat2','stat3']

    def is_exist(self):
        return 1

    def read(self,start_addr,data_length):
        start_addr=((start_addr & 0xff00 )>>8),(start_addr& 0x00ff)
        data_length=((data_length & 0xff00) >>8),(data_length & 0x00ff)
        command=[self.addr,0x03,*start_addr,*data_length]
        self.ser.write(bytearray(addcrc(command)))
        re=list(self.ser.read(3))
        re=re+list(self.ser.read(re[-1]+2))
        return [(re[3+2*i]<<8)+re[2*i+4] for i in range(0,(re[2])//2)]

    def  read_bytes(self,start_addr,reg_num):
        start_addr=((start_addr & 0xff00 )>>8),(start_addr& 0x00ff)
        data_length=((reg_num & 0xff00) >>8),(reg_num & 0x00ff)
        command=[self.addr,0x03,*start_addr,*data_length]
        self.ser.write(bytearray(addcrc(command)))
        re=list(self.ser.read(3))
        re=re+list(self.ser.read(re[-1]+2))
        print('re',re)
        return [re[i]  for i in range(3,re[2]+3)]
        
    def refresh(self):
        self.bitmap=0
        for i in range(0,4):
            self.bitmap=(self.bitmap<<16)+(byte_reverser( (self.read_group(i)[0]&0xff00 )  >>8) <<8)+byte_reverser(self.read_group(i)[0]&0xff)
        
        self.dev_offset=[ i for i in range(0,64) if ((self.read(4+i*2,2)[0]<<8)+self.read(4+i*2,2)[-1] )  !=0  and i<20 ]
        self.dev_uuid=[ (self.read(4+i*2,2)[0]<<8)+self.read(4+i*2,2)[-1] for i in self.dev_offset]
        self.dev_map={self.dev_uuid[i]:self.dev_offset[i]  for i in range(0,len(self.dev_offset))}
        self.dev_reg_description=['sensor0','sensor1','sensor2','sensor3','dev_bat_H','dev_bat_L','stat0','stat1','stat2','stat3']

    def read_device(self,dev_offset): 
        data_start=132
        raw=self.read(132+dev_offset*14,14)
        print(raw)
        data=[]
        for i in range(0,len(raw)) :
            if i < 8:
                if i in [0,2,4,6]:
                    data.append(raw[i])
                else:
                    data[-1]=(data[-1]<<16)+raw[i]
            else:
                data=data+[raw[i]]
        print(data)
        return {self.dev_reg_description[i]:data[i] for i in range(0,len(data))}
    
    def read_all(self):
        return  { "%#06X" % i :self.read_device(i) for i in self.dev_offset}
    
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

    def write_reg(self,addr,data):
        addr=((addr & 0xff00) >>8),(addr & 0x00ff)
        data=((data & 0xff00) >>8),(data & 0x00ff)
        command=[self.addr,0x06,*start_addr,*data]
        self.ser.write(bytearray(addcrc(command)))
        re=list(self.read(3))
        re=re+list(self.ser.read(re[-1]+2))

        if re == addcrc(command):
            return 0
        else:
            return 1
        

    def write_reg_group(self,addr,data):
        pass 
        
    

    