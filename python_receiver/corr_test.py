import numpy as np
import matplotlib.pyplot as plt

from receiver import Receiver

source = "sample_gen_example1.txt"
sampling_rate = 8       # kHz --> fake sampling rate of 2000 Hz or 8000 Hz
frame_size = 128        # #samples
frame_length = frame_size / (sampling_rate * 1000)  # ms

r = Receiver(source, use_file=True)
data = r.receive(frame_size)

N = frame_size
T = 1/(sampling_rate * 1000)
x = np.linspace(0, N*T, N)
# y = np.sin(2*np.pi*440*x)
y_a = data[:,1]
y_b = data[:,2]

yc = np.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
lag_sample_delay = yc.argmax() - (len(y_a) - 1)
incident_mic = 'both' if lag_sample_delay == 0 else ('mic_A' if lag_sample_delay < 0 else 'mic_B')
lag_time_delay = abs(lag_sample_delay) * frame_length / frame_size
xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
xc = xc * frame_length / frame_size    # in ms


print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
print("Time Delay/Lag: {} ms".format(lag_time_delay))
print("Incident Mic: {}".format(incident_mic))

print(lag_time_delay, yc[lag_sample_delay])
plt.ylabel("Correlation")
plt.xlabel("Delay/Lag")
plt.plot(xc, yc, marker='o')
plt.annotate('argmax={}@{}ms'.format(round(yc[lag_sample_delay], 3), lag_time_delay),  (lag_time_delay, yc[yc.argmax()]), ha='center')
plt.show()


# N = 4096
# t = np.linspace(0, N * 1/2000 * N)
# s = data[:, 1]  # get first column

# fft = np.fft.fft(s)
# fftfreq = np.fft.fftfreq(len(s))
# T = t[1] - t[0]

# f = np.linspace(0, 1 / T, N)
# plt.ylabel("Amplitude")
# plt.xlabel("Frequency [Hz]")
# plt.plot(fftfreq, fft)
# plt.show()

