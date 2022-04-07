import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from receiver import Receiver

source = "sample_gen_example1_24kHz_800Hz_0.0007ms.txt"
sampling_rate = 24      # kHz --> fake sampling rate of 2000 Hz or 8000 Hz
frame_size = 192        # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 260      # mm
filter_lowcut = 500.0
filter_highcut = 1100.0
frame_length = frame_size / (sampling_rate * 1000)  # ms

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

r = Receiver(source, use_file=True)
data = r.receive(frame_size)

N = frame_size
T = 1/(sampling_rate * 1000)
x = np.linspace(0, N*T, N)
y_a_pre = data[:,0]
y_b_pre = data[:,1]

# filtering
fs = sampling_rate * 1000
y_a = butter_bandpass_filter(y_a_pre, filter_lowcut, filter_highcut, fs, order=12)
y_b = butter_bandpass_filter(y_b_pre, filter_lowcut, filter_highcut, fs, order=12)

# correlation
yc = signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
lag_sample_delay = yc.argmax() - (len(y_a) - 1)
lag_time_delay = abs(lag_sample_delay) * frame_length / frame_size      # unit is in seconds
xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
xc = xc * frame_length / frame_size    # in ms

incident_mic = 'both' if lag_sample_delay == 0 else ('mic_A' if lag_sample_delay < 0 else 'mic_B')
incident_angle = (180.0 / math.pi) * math.acos(speed_sound * (lag_time_delay) / (mic_distance / 1000))

print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
print("Time Delay/Lag: {} ms".format(lag_time_delay))
print("Correlation: {}".format(round(yc[lag_sample_delay], 3)))
print("Incident Mic: {}".format(incident_mic))
print("Incident Angle: {}deg".format(round(incident_angle, 3)))

fig, ax1 = plt.subplots()
ax1.set_xlabel("Sample")
ax1.set_ylabel("Original Signal")
ax1.plot(x, y_a_pre, color='red', marker='o')
ax1.plot(x, y_b_pre, color='blue', marker='o')
ax1.tick_params(axis='y')
ax2 = ax1.twinx()
ax2.set_ylabel("Filtered Signal")
ax2.plot(x, y_a, color='purple')
ax2.plot(x, y_b, color='green')
ax2.tick_params(axis='y')
fig.tight_layout()
plt.show()

plt.ylabel("Correlation")
plt.xlabel("Delay/Lag")
plt.plot(xc, yc, marker='o')
plt.annotate('argmax={}@{}ms'.format(round(yc[lag_sample_delay], 3), lag_time_delay),  (lag_time_delay, yc[yc.argmax()]), ha='center')
plt.show()