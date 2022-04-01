import numpy as np
import scipy.fftpack
from cmath import pi
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
y = data[:,2]

yf = scipy.fftpack.fft(y)
xf = np.linspace(0, 1//(2*T), N//2)

plt.ylabel("Amplitude")
plt.xlabel("Frequency [Hz]")
plt.plot(xf, 2/N * np.abs(yf[:N//2]))
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

