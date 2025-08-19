from multiprocess import Manager as m
from multiprocess import Process as p
import pyserial as ser
def getdata(ser_addr,baud,addr):
	addr_chn={0x01:8,0x02:7,0x03:6,0x04:5,0x05:4,0x06,3,0x07:2,0x08:1}
	ser=ser.()
