import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from receiver import Receiver

source_use_file = False
source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "sample_gen_example1_24kHz_800Hz_0.0003ms.txt"
sampling_rate = 32      # kHz
frame_size = 1024       # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 260      # mm
repeat = True
frame_length = frame_size / (sampling_rate * 1000)  # sec

r = Receiver(source, use_file=source_use_file)

first = True
incident_angle = 90
fig, (ax1, ax2) = plt.subplots(2)
while first or repeat:
    data = r.receive(frame_size)

    N = frame_size
    T = 1/(sampling_rate * 1000)
    x = np.linspace(0, N*T, N)
    y_a = data[:,0]
    y_b = data[:,1]

    # test: normalize??
    y_a = (y_a - np.mean(y_a)) / np.std(y_a)
    y_b = (y_b - np.mean(y_b)) / np.std(y_b)

    yc = signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
    lag_sample_delay = yc.argmax() - (len(y_a) - 1)
    lag_time_delay = abs(lag_sample_delay) * frame_length / frame_size
    xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
    xc = xc * frame_length / frame_size    # in sec

    incident_mic = 'both' if lag_sample_delay == 0 else ('mic_A' if lag_sample_delay < 0 else 'mic_B')
    try:
        new_incident_angle = (180.0 / math.pi) * math.acos(speed_sound * (lag_time_delay) / (mic_distance / 1000))
    except:
        new_incident_angle = incident_angle
    incident_angle = new_incident_angle

    print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
    print("Time Delay/Lag: {} ms".format(lag_time_delay))
    print("Correlation: {}".format(round(yc[lag_sample_delay], 3)))
    print("Incident Mic: {}".format(incident_mic))
    print("Incident Angle: {}deg".format(round(incident_angle, 3)))

    ax1.cla()
    ax1.set_ylabel("Correlation")
    ax1.set_xlabel("Delay/Lag")
    ax1.plot(xc, yc)
    # ax1.plot(xc, yc, marker='o')
    ax1.annotate('argmax={}@{}ms'.format(round(yc[lag_sample_delay], 3), lag_time_delay),  (lag_time_delay, yc[yc.argmax()]), ha='center')
    
    ax2.cla()
    ax2.set_ylabel("Sample Value")
    ax2.set_xlabel("Sample #")
    ax2.plot(x, y_a, color='red')
    ax2.plot(x, y_b, color='blue')

    plt.pause(0.25)

    first = False

plt.show()

