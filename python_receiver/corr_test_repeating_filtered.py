import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from receiver import Receiver

source = "COM27"
sampling_rate = 8       # kHz --> fake sampling rate of 2000 Hz or 8000 Hz
frame_size = 192        # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 100      # mm
frame_length = frame_size / (sampling_rate * 1000)  # ms

def butter_bandpass(lowcut, highcut, fs, order=5):
    return signal.butter(order, [lowcut, highcut], fs=fs, btype='band')

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = signal.lfilter(b, a, data)
    return y

r = Receiver(source, use_file=False)

while True:
    data = r.receive(frame_size)

    N = frame_size
    T = 1/(sampling_rate * 1000)
    x = np.linspace(0, N*T, N)
    y_a = data[:,0]
    y_b = data[:,1]

    # filtering
    fs = sampling_rate * 1000
    lowcut = 500.0
    highcut = 1000.0
    y_a = butter_bandpass_filter(y_a, lowcut, highcut, fs, order=6)
    y_b = butter_bandpass_filter(y_b, lowcut, highcut, fs, order=6)

    yc = signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
    lag_sample_delay = yc.argmax() - (len(y_a) - 1)
    lag_time_delay = abs(lag_sample_delay) * frame_length / frame_size
    xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
    xc = xc * frame_length / frame_size    # in ms

    incident_mic = 'both' if lag_sample_delay == 0 else ('mic_A' if lag_sample_delay < 0 else 'mic_B')
    incident_angle = (180.0 / math.pi) * math.acos(speed_sound * (lag_time_delay / 1000) / (mic_distance / 1000))

    print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
    print("Time Delay/Lag: {} ms".format(lag_time_delay))
    print("Correlation: {}".format(round(yc[lag_sample_delay], 3)))
    print("Incident Mic: {}".format(incident_mic))
    print("Incident Angle: {}deg".format(round(incident_angle, 3)))

    # plt.ylabel("Correlation")
    # plt.xlabel("Delay/Lag")
    # plt.plot(xc, yc, marker='o')
    # plt.annotate('argmax={}@{}ms'.format(round(yc[lag_sample_delay], 3), lag_time_delay),  (lag_time_delay, yc[yc.argmax()]), ha='center')
    # plt.show()

