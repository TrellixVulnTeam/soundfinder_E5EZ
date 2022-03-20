import time
import serial
arduinoData = serial.Serial('com3', 115200)
time.sleep(1)
while True:
    while(arduinoData.inWaiting()==0):
        pass
    dataPacket=arduinoData.readline()
    dataPacket=str(dataPacket, 'utf-8')
    dataPacket=dataPacket.strip('\r\n')
    print(dataPacket)