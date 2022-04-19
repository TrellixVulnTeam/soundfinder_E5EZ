import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from receiver import Receiver

source_use_file = False   # use device or file
source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "sample_gen_example1_24kHz_800Hz_0.0003ms.txt"
sampling_rate = 32        # kHz
frame_size = 1024         # #samples
speed_sound = 343         # 343 m/sec = speed of sound in air
mic_distance = 260        # mm
average_delays = 3        # rolling average on sample delay (set to 0 for none)
filter_on = True          # butterworth bandpass filter
filter_lowcut = 500.0     # Hz
filter_highcut = 1100.0   # Hz
filter_order = 12         # filter order
repeat = True             # sample repeatedly or once
graph_samples = True      # generate plot (takes more time)
frame_length = frame_size / (sampling_rate * 1000)  # sec

r = Receiver(source, use_file=source_use_file)

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = signal.butter(order, [low, high], analog=False, btype='band', output='sos')
    return sos

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    sos = butter_bandpass(lowcut, highcut, fs, order=order)
    y = signal.sosfilt(sos, data)
    return y

first = True
incident_angle = 90
fig, (ax1, ax2) = plt.subplots(2)
lag_sample_delay_rolling_avg = []

while first or repeat:
    data = r.receive(frame_size)

    N = frame_size
    T = 1/(sampling_rate * 1000)
    x = np.linspace(0, N*T, N)
    y_a = data[:,0]
    y_b = data[:,1]

    if filter_on:
        y_a = butter_bandpass_filter(y_a, filter_lowcut, filter_highcut, sampling_rate * 1000, order=filter_order)
        y_b = butter_bandpass_filter(y_b, filter_lowcut, filter_highcut, sampling_rate * 1000, order=filter_order)

    # # normalize or not
    # y_a = (y_a - np.mean(y_a)) / np.std(y_a)
    # y_b = (y_b - np.mean(y_b)) / np.std(y_b)

    yc = signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
    lag_sample_delay = yc.argmax() - (len(y_a) - 1)
    if average_delays > 0: # rolling average on sample delays
        lag_sample_delay_rolling_avg.append(lag_sample_delay)
        if len(lag_sample_delay_rolling_avg) > average_delays:
            lag_sample_delay_rolling_avg = lag_sample_delay_rolling_avg[1:]
        lag_sample_delay = math.ceil(np.mean(lag_sample_delay_rolling_avg))

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
    # print(lag_sample_delay_rolling_avg)

    if graph_samples:
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

