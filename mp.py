from multiprocess import Manager as m
from multiprocess import Process as p
import pyserial as ser
def getdata(ser_addr,baud,chn):
	addr_chn={0x01:8,0x02:7,0x03:6,0x04:5,0x05:4,0x06,3,0x07:2,0x08:1}
	chn_addr=(lambda x : {v:k for k,v in x.iteritems()})(addr_chn)
	ser=ser.Serial(ser_addr,baud)
	comms={'read':[chn_addr[chn],0x03,0x0E,]}
