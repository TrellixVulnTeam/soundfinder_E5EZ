#AudioImagingIntegration
#WiP
import serial
import math
import numpy as np
import matplotlib.pyplot as plt
#import haarCascade
from scipy import signal

from receiver import Receiver

from cross_corr_func import getAngle

#source = "COM4"
#r = Receiver(source, use_file=False)
sampling_rate = 24 #kHz
frame_size = 216 
mic_distance = 260 #mm
current_angle = 0   #degrees -900 to 900

tm4c = serial.Serial("COM3", 115200)    #adjust port as needed

while True:
    #incident_angle, incident_mic = getAngle(r, sampling_rate, frame_size, mic_distance)
    #if incident_mic == 'mic_B':
        #incident_angle = -incident_angle    #
    print("foo")

    imaging_angle = 25  #test value
    #imaging_angle = (call an angle getting func from haarCascade)
    incident_angle = 50    #testing
    incident_mic = 'B'

    tm4c.write(b'B')
    tm4c.write(incident_angle * 10)
    # if (abs(incident_angle - imaging_angle)) >= 15:
    #     #turn towards audio angle; need to send an angle over serial to the motor-controlling tm4c
    #     if incident_mic == 'mic_B':
    #         tm4c.write(b'B')
    #     else:
    #         tm4c.write(b'A')
    #     tm4c.write(incident_angle * 10)   #since motor control functions of increments of a tenth of a degree (900 = 90 degrees)
    #     #wait for write back to confirm motor has turned?
    #     #confirmTurn = tm4c.readline()
    #     #if confirmTurn == 'confirm':
    #         #print('turned towards audio angle')

    # else:
    #     #stay on camera
    #     print('staying on camera')
