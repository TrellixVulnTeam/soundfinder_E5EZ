# fft.py
# Library for detecting the direction of sound
import numpy as np
import scipy.fftpack
import matplotlib.pyplot as plt

from receiver import Receiver

class FFT:
    frame_size = 0
    sampling_rate = 0
    period = 1/(sampling_rate)

    def __init__(self, frame_size=128, sampling_rate=8000):
        self.frame_size = frame_size
        self.sampling_rate = sampling_rate

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
