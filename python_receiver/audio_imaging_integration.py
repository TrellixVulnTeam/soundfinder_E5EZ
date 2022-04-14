#AudioImagingIntegration
#WiP
import serial
import math
import numpy as np
import matplotlib.pyplot as plt
import haarCascade
from scipy import signal

from receiver import Receiver

from cross_corr_func import getAngle

source = "sample_gen_example1_24kHz_800Hz_0.0003ms.txt"
r = Receiver(source, use_file=True)
sampling_rate = 24 #kHz
frame_size = 216 
mic_distance = 260 #mm

tm4c = serial.Serial('COM5')    #adjust port as needed

while True:
    incident_angle, incident_mic = getAngle(r, sampling_rate, frame_size, mic_distance)
    if incident_mic == 'mic_B':
        incident_angle = -incident_angle    #

    imaging_angle = 60  #test value
    #imaging_angle = (call an angle getting func from haarCascade)

    if (incident_angle - imaging_angle) >= 15:
        #turn towards audio angle; need to send an angle over serial to the motor-controlling tm4c
        serial.write(incident_angle * 10)   #since motor control functions of increments of a tenth of a degree (900 = 90 degrees)
        #wait for write back to confirm motor has turned?
        confirmTurn = tm4c.readline()
        if confirmTurn == 'confirm':
            print('turned towards audio angle')

    else:
        #stay on camera
        print('staying on camera')
