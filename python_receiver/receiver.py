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

    eng = None

    MAX_SAMPLES = 1024  # 216  # 192



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
            if len(raw_data) != 2:
                break
            data[i] = raw_data  # blocking
            # print(data[i])
            i = i + 1

        # s.serial_port.close()

        return data


    def filter_single_section(self, data):
        b = [0.778730,-6.999374,27.969952,-65.220416,97.798538,-97.798538,65.220416,-27.969952,6.999374,-0.778730]
        a = [1.000000,-8.500584,32.119986,-70.800841,100.320634,-94.748844,59.639089,-24.121272,5.687301,-0.595469]
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

    def filter(self, data):
        # SOS =
        # [
        #     [1.0000, -0.9983, 0, 1.0000, -0.6942, 0],
        #     [1.0000, -2.0034, 1.0043, 1.0000, -1.8673, 0.8911],
        #     [1.0000, -1.9913, 0.9939, 1.0000, -1.9631, 0.9731],
        #     [1.0000, -2.0025, 1.0064, 1.0000, -1.9843, 0.9913],
        #     [1.0000, -1.9927, 0.9972, 1.0000, -1.9917, 0.9979]
        #
        # ]

        SOS = np.zeros((5, 6))
        SOS[0] = [1.0000, -0.9983, 0, 1.0000, -0.6942, 0]
        SOS[1] = [1.0000, -2.0034, 1.0043, 1.0000, -1.8673, 0.8911]
        SOS[2] = [1.0000, -1.9913, 0.9939, 1.0000, -1.9631, 0.9731]
        SOS[3] = [1.0000, -2.0025, 1.0064, 1.0000, -1.9843, 0.9913]
        SOS[4] = [1.0000, -1.9927, 0.9972, 1.0000, -1.9917, 0.9979]

        G = [0.778730,1.000000,1.000000,1.000000,1.000000,1.000000]

        # SOS = signal.ellip(13, 1, 80, 0.1, output='sos', fs=8)

        # print(SOS)

        return np.prod(G)*signal.sosfilt(SOS, data)

    def start_matlab(self):
        import matlab.engine
        self.eng = matlab.engine.start_matlab()

    def matlab_filter(self, samples):
        out = self.eng.filter_1(samples)
        return out


if __name__ == "__main__":

    # r = Receiver("COM27")
    r = Receiver("sin-unfiltered", use_file=True)
    r.start_matlab()
    data = r.receive(216)

    # plt.plot(data[:,1], "b")
    # plt.plot(data[:,2], "r")
    # plt.show()

    N = 216

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
    # data = r.receive(216)
    #
    # # plt.plot(data[:,1], "b")
    # # plt.plot(data[:,2], "r")
    # # plt.show()
    #
    # N = 216
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
