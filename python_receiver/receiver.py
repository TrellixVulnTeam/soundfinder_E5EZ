import serial
import numpy as np
import scipy.fftpack
from scipy import signal
import matplotlib.pyplot as plt

class Receiver:
    """
    Receives data from microcontroller
    """
    source = None
    use_file = None
    baud_rate = None

    serial_port = None

    MAX_SAMPLES = 192



    def __init__(self, source: str, use_file=False, baud_rate=115200) -> np.array:
        """
        Connects to device, receives a number of samples, and returns them
        """

        self.source = source
        self.use_file = use_file
        self.baud_rate = baud_rate

        if self.use_file is True:
            self.serial_port = open(self.source, "rb")
        else:
            self.serial_port = serial.Serial(self.source, self.baud_rate, timeout=1, write_timeout=1)
    

    def receive(self, num_samples: int) -> np.array:
        """
        Receives specified number of lines of data
        """


        if num_samples > self.MAX_SAMPLES:
            raise ValueError(f'Cannot receive more than {self.MAX_SAMPLES}')

        i = 0
        data = np.zeros((num_samples, 2), dtype=np.uint)

        # print("pog")

        if not self.use_file:
            self.serial_port.flushInput()


        # Wait for the start character
        while True:
            before_split = self.serial_port.readline()
            # print(before_split)
            raw_data = before_split.split()

            # print(raw_data[0])
            # print(raw_data)
            if len(raw_data) >= 1:
                if raw_data[0] == b's':
                    break
            
        while i < num_samples:


            raw_data = self.serial_port.readline().split()  # blocking
            # print(raw_data)
            data[i] = raw_data  # blocking
            # print(data[i])
            i = i + 1

        # s.serial_port.close()

        return data


    def filter(self, data):
        b = [0.001134,-0.014390,0.087372,-0.335444,0.905163,-1.799220,2.665252,-2.851675,1.884637,-0.000000,-1.884637,2.851675,-2.665252,1.799220,-0.905163,0.335444,-0.087372,0.014390,-0.001134]
        a = [1.000000,-14.688676,104.433693,-476.896409,1565.851943,-3922.706308,7765.854993,-12417.589951,16253.031782,-17540.539935,15644.740702,-11505.422199,6925.971668,-3367.416178,1293.821638,-379.276046,79.942807,-10.822757,0.709247]
        # # b, a = signal.iirfilter(17, [2*np.pi*50, 2*np.pi*200], rp=1, rs=60, btype='band', ftype='ellip', fs=2*np.pi*8000)
        # w, h = signal.freqs(b, a, 8000)
        # fig = plt.figure()
        # ax = fig.add_subplot(1, 1, 1)
        # ax.semilogx(w / (2*np.pi), 20 * np.log10(np.maximum(abs(h), 1e-5)))
        # ax.set_title('Chebyshev Type II bandpass frequency response')
        # ax.set_xlabel('Frequency [Hz]')
        # ax.set_ylabel('Amplitude [dB]')
        # ax.axis((10, 1000, -100, 10))
        # ax.grid(which='both', axis='both')
        # plt.show()

        # do filtering
        return signal.lfilter(b, a, data)


if __name__ == "__main__":

    r = Receiver("COM27")
    data = r.receive(192)

    data = r.receive(192)

    # plt.plot(data[:,1], "b")
    # plt.plot(data[:,2], "r")
    # plt.show()

    N = 192

    T = 1/8000 # fake sampling rate of 2000 Hz

    x = np.linspace(0, N*T, N)
    y = data[:,1]
    # y = np.sin(2*np.pi*440*x)

    yf = scipy.fftpack.fft(y)
    xf= np.linspace(0, 1//(2*T), N//2)

    plt.ylabel("Amplitude")
    plt.xlabel("Frequency [Hz]")
    plt.plot(xf, 2/N * np.abs(yf[:N//2]))
    plt.show()



    #
    # # r = Receiver("test_data", use_file=True)
    #
    # # data = r.receive(10)
    #
    # # print(data)
    #
    # # r = Receiver("COM27")
    # r = Receiver("run1", use_file=True)
    #
    # data = r.receive(192)
    #
    # # plt.plot(data[:,1], "b")
    # # plt.plot(data[:,2], "r")
    # # plt.show()
    #
    # N = 192
    #
    # T = 1/2000 # fake sampling rate of 2000 Hz
    #
    # x = np.linspace(0, N*T, N)
    # y = data[:,2]
    # # y = np.sin(2*np.pi*440*x)
    #
    # yf = scipy.fftpack.fft(y)
    # xf= np.linspace(0, 1//(2*T), N//2)
    #
    # plt.ylabel("Amplitude")
    # plt.xlabel("Frequency [Hz]")
    # plt.plot(xf, 2/N * np.abs(yf[:N//2]))
    # plt.show()
    #
    # # np.savetxt("run1", data, delimiter=" ", fmt="%u")
