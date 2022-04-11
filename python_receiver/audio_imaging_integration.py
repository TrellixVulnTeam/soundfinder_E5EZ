#AudioImagingIntegration
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

while True:
    incident_angle, incident_mic = getAngle(r, sampling_rate, frame_size, mic_distance)
    if incident_mic == 'mic_B':
        incident_angle = 180 - incident_angle    #

    imaging_angle = 60  #test value
    #imaging_angle = (call an angle getting func from haarCascade)

    if (incident_angle - imaging_angle) >= 15:
        #turn towards audio angle
        print('turning towards audio angle')

    else:
        #stay on camera
        print('staying on camera')
