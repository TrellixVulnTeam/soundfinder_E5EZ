# fft.py
# Library for detecting the direction of sound
import numpy as np
import scipy.fftpack
import matplotlib.pyplot as plt
import matlab.engine

from receiver import Receiver


class FFT:
    frame_size = 0
    sampling_rate = 0
    period = 0

    def __init__(self, frame_size=192, sampling_rate=8000):
        self.frame_size = frame_size
        self.sampling_rate = sampling_rate
        self.period = 1/self.sampling_rate

    def fft(self, ch1_data, ch2_data):
        """
        Performs FFT on 2 channels of data
        Input: 1D array
        Output: 3 arrays with x values, and 2 y values
        """
        x = np.linspace(0, self.frame_size*self.sampling_rate, self.frame_size)

        yf1 = scipy.fftpack.fft(ch1_data)
        yf2 = scipy.fftpack.fft(ch2_data)
        xf = np.linspace(0, 1//(2*self.period), self.frame_size//2)

        return xf, yf1, yf2

    def graph_fft_data(self, xf, yf1, yf2):
        """
        Graphs FFT data
        """
        plt.ylabel("Amplitude")
        plt.xlabel("Frequency [Hz]")
        plt.plot(xf, 2/self.frame_size * np.abs(yf1[:self.frame_size//2]), 'b')
        plt.plot(xf, 2 / self.frame_size * np.abs(yf2[:self.frame_size // 2]), 'r')
        plt.show()


if __name__ == "__main__":
    # fft = FFT(sampling_rate=32000)
    fft = FFT()
    # receiver = Receiver("COM27")
    receiver = Receiver("sin-unfiltered", use_file=True)
    receiver.start_matlab()

    data = receiver.receive(192)

    # filter
    # ch1 = receiver.filter(data[:,0])
    # ch2 = receiver.filter(data[:,1])

    ch1 = receiver.matlab_filter(matlab.uint16(data[:,0].tolist()))
    ch2 = receiver.matlab_filter(matlab.uint16(data[:,1].tolist()))
    # ch1 = ch1.toarray()
    # ch2 = ch2.toarray()
    print(ch1)

    t = np.linspace(0, 1/8000, 192)
    plt.plot(t, data[:,0], 'b')
    plt.plot(t, data[:,1], 'r')
    plt.show()

    plt.plot(t, ch1[0], 'b')
    plt.plot(t, ch2[0], 'r')
    plt.show()

    xf, yf1, yf2 = fft.fft(data[:,0], data[:,1])
    xf_filter, yf1_filter, yf2_filter = fft.fft(ch1, ch2)

    fft.graph_fft_data(xf, yf1, yf2)

    fft.graph_fft_data(xf_filter, yf1_filter[0], yf2_filter[0])

    # np.savetxt("pog", data, delimiter=" ", fmt="%u")
