from cmath import pi
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack

from receiver import Receiver

r = Receiver("random_data", use_file=True)

data = r.receive(4096)

N = 4096

T = 1/2000 # fake sampling rate of 2000 Hz

x = np.linspace(0, N*T, N)
# y = data[:,1]
y = np.sin(2*np.pi*440*x)

yf = scipy.fftpack.fft(y)
xf= np.linspace(0, 1//(2*T), N//2)

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

