import math
import numpy as np
import scipy.signal
import scipy.fftpack
import matplotlib.pyplot as plt

if __name__ == "__main__":
    from receiver import Receiver
else:
    from audio.python_receiver.receiver import Receiver

# SoundFinder class
class SoundFinder:
    """
    Finds the source direction of sound given two audio signals 
    """

    def __init__(self, receiver: Receiver, sampling_rate = 32, frame_size = 1024, mic_distance = 250, normalize_sig = True, filter_bounds = None, average_delays = 0, left_mic = 'mic_A', angle_calibration = [90, 10], log_output = False, graph_samples = False, graph_size = (8, 7)):
        # print(sampling_rate, frame_size, mic_distance, normalize_sig, filter_bounds, average_delays, angle_calibration, log_output, graph_samples , graph_size)
        # sampling & correlation settings
        self.sampling_rate = sampling_rate      # kHz  -  MUST MATCH ESP/TM4C
        self.frame_size = frame_size            # #samples  -  MUST MATCH ESP/TM4C
        self.frame_length = frame_size / (sampling_rate * 1000)  # sec
        self.mic_distance = mic_distance        # mm  -  MUST MATCH SETUP
        self.filter_on = not(filter_bounds == None or filter_bounds == False)   # butterworth bandpass filter
        self.filter_lowcut = filter_bounds[0] if filter_bounds else 0.0    # Hz
        self.filter_highcut = filter_bounds[1] if filter_bounds else 2000.0 # Hz
        self.filter_order = filter_bounds[2] if filter_bounds else 1       # filter order
        self.average_delays = average_delays    # rolling average on sample delay (set to 0 for none)
        self.graph_samples = graph_samples      # generate plot (takes more time)
        self.angle_edge_calib = angle_calibration[1]              #25 # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45)
        self.angle_middle_calib = angle_calibration[0]            # observed incident angle middle (should be 90)
        self.normalize_signal = normalize_sig   # normalize before correlation
        self.left_mic = left_mic
        # instance fields
        self.r = receiver                       # serial dataframe receiver (import from receiver.py)
        self.speed_sound = 343                  # 343 m/sec = speed of sound in air
        self.frame_counter = 0                  # frame counter
        self.incident_angle = 90                # initial value
        self.lag_sample_delay_rolling_avg = []  # rolling avg array
        self.log_output = log_output
        # output values
        self.data = None                        # current/last signal data frame
        self.lag_sample_delay = 0
        self.lag_time_delay = 0
        self.incident_mic = None
        self.incident_angle = 0
        self.fine_tuned_incident_angle = self.incident_angle
        # graphing
        self.fig = None
        if self.graph_samples:
            # cache plots for easy/fast redrawing
            fig, (ax1, ax2, ax3) = plt.subplots(3, figsize=graph_size, num="SoundFinder")
            self.fig = fig
            self.ax1 = ax1
            self.ax2 = ax2
            self.ax3 = ax3

    # get next/current angle and incident mic
    def next_angle(self):

            # filter utility functions
        def butter_bandpass(lowcut, highcut, fs, order=5):
            nyq = 0.5 * fs
            low = lowcut / nyq
            high = highcut / nyq
            sos = scipy.signal.butter(order, [low, high], analog=False, btype='band', output='sos')
            return sos
        def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
            sos = butter_bandpass(lowcut, highcut, fs, order=order)
            y = scipy.signal.sosfilt(sos, data)
            return y

        # receive 1 data frame
        self.data = self.r.receive(self.frame_size)
        # print(len(self.data))
        # print(self.data)
        self.frame_counter += 1

        # preprocess signal data
        N = self.frame_size
        T = 1/(self.sampling_rate * 1000)
        x = np.linspace(0, N*T, N)
        y_a = self.data[:,0]
        y_b = self.data[:,1]
        # normalize signal data if chosen
        if self.normalize_signal:
            y_a = (y_a - np.mean(y_a)) / np.std(y_a)
            y_b = (y_b - np.mean(y_b)) / np.std(y_b)
        # filter signal data if chosen
        if self.filter_on:
            y_a = butter_bandpass_filter(y_a, self.filter_lowcut, self.filter_highcut, self.sampling_rate * 1000, order=self.filter_order)
            y_b = butter_bandpass_filter(y_b, self.filter_lowcut, self.filter_highcut, self.sampling_rate * 1000, order=self.filter_order)

        # perform fft
        yf_a = scipy.fftpack.fft(y_a)
        yf_b = scipy.fftpack.fft(y_b)
        xf = np.linspace(0, 1//(2*T), N//2)

        # correlate signals & calculate signal lag
        yc = scipy.signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
        # extract sample delay from correlation graph
        self.lag_sample_delay = yc.argmax() - (len(y_a) - 1)
        # rolling average on sample delays if chosen (smooths out outliers/noise)
        if self.average_delays > 0:
            self.lag_sample_delay_rolling_avg.append(self.lag_sample_delay)
            if len(self.lag_sample_delay_rolling_avg) > self.average_delays:
                self.lag_sample_delay_rolling_avg = self.lag_sample_delay_rolling_avg[1:]
            self.lag_sample_delay = math.ceil(np.mean(self.lag_sample_delay_rolling_avg))
        # calculate time delay from sample delay
        self.lag_time_delay = abs(self.lag_sample_delay) * self.frame_length / self.frame_size
        # generate x-axis (in either sample or time delay) to make sense of correlation graph
        xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
        xc = xc * self.frame_length / self.frame_size    # in sec

        # determine which mic the sound hit first
        self.incident_mic = 'both' if self.lag_sample_delay == 0 else ('mic_A' if self.lag_sample_delay < 0 else 'mic_B')
        # calculate sound source angle of arrival using time delay, speed of sound, and mic distance
        new_incident_angle = 0
        try:  # try-catch needed for arccos domain errors (probably noisy outlier delay values whose source angle would be out of range/impossible)
            new_incident_angle = (180.0 / math.pi) * math.acos(self.speed_sound * (self.lag_time_delay) / (self.mic_distance / 1000))
        except:
            new_incident_angle = self.incident_angle
        self.incident_angle = new_incident_angle

        # fine-tune value with calibration incident angle edge (extrapolate range)
        self.fine_tuned_incident_angle = self.incident_angle
        # if self.angle_edge_calib != 0:
        #     angle_val = self.incident_angle
        #     if angle_val < self.angle_edge_calib:
        #         angle_val = self.angle_edge_calib
        #     self.fine_tuned_incident_angle = self.angle_middle_calib - (self.angle_middle_calib * ((self.angle_middle_calib - angle_val) / (self.angle_middle_calib - self.angle_edge_calib)))

        # output relevant data
        if self.log_output:
            print("{} @ {}deg <-- {}deg <-- d={}ms,{}sam@c{}".format(self.incident_mic, round(self.fine_tuned_incident_angle, 3), round(self.incident_angle, 3), self.lag_time_delay, self.lag_sample_delay, round(yc[self.lag_sample_delay], 3)))
            # print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
            # print("Time Delay/Lag: {} ms".format(lag_time_delay))
            # print("Correlation: {}".format(round(yc[lag_sample_delay], 3)))
            # print("Incident Mic: {}".format(incident_mic))
            # print("Incident Angle: {}deg".format(round(incident_angle, 3)))
            # print("Fine-Tuned Incident Angle: {}deg".format(round(fine_tuned_incident_angle, 3)))
            # print(lag_sample_delay_rolling_avg)

        # graph signal alongside correlation if chosen
        if self.graph_samples:
            # graph signal
            self.ax1.cla()
            self.ax1.set_title("Signal Frame")
            self.ax1.set_ylabel("Sample Value")
            self.ax1.set_xlabel("Sample #")
            self.ax1.plot(x, y_a, color='red')
            self.ax1.plot(x, y_b, color='blue')
            # graph correlation
            self.ax2.cla()
            self.ax2.set_title("Correlation: {} @ {}°".format(self.incident_mic, round(self.fine_tuned_incident_angle, 3)))
            self.ax2.set_ylabel("Correlation")
            self.ax2.set_xlabel("Delay/Lag")
            self.ax2.plot(xc, yc)  # marker='o')
            self.ax2.annotate('argmax={}@{}ms'.format(round(yc[self.lag_sample_delay], 3), self.lag_time_delay),  (self.lag_time_delay, yc[yc.argmax()]), ha='center')
            # graph fft
            self.ax3.cla()
            self.ax3.set_title("Fourier Transform")
            self.ax3.set_ylabel("Amplitude")
            self.ax3.set_xlabel("Frequency [Hz]")
            self.ax3.plot(xf, 2/N * np.abs(yf_a[:N//2]))
            self.ax3.plot(xf, 2/N * np.abs(yf_b[:N//2]))

            self.fig.tight_layout()
            plt.pause(0.25) # live periodic update
            #plt.savefig("./graphs/correlation_output_{}.png".format(self.frame_counter))

        return (self.fine_tuned_incident_angle, self.incident_mic)

    def convert_angle(self, angle, mic):
        angle_invert = 90 - angle
        if not (mic == self.left_mic):
            angle_invert *= -1
        return angle_invert



# entry point
if __name__ == "__main__":

    # sampling & correlation settings
    source_use_file = False   # use device or file
    source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "data/sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
    sampling_rate = 32        # kHz  -  MUST MATCH ESP
    frame_size = 768          # #samples  -  MUST MATCH ESP
    mic_distance = 250        # mm  -  MUST MATCH SETUP
    average_delays = 5        # rolling average on sample delay (set to 0 for none)
    normalize_signal = True   # normalize before correlation
    filter_on = True          # butterworth bandpass filter
    filter_lowcut = 500.0     # Hz
    filter_highcut = 1300.0   # Hz
    filter_order = 12         # filter order
    repeat = True             # sample forever or only once
    graph_samples = True      # generate plot (takes more time)
    angle_edge_calib = 25  #25 # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45)
    angle_middle_calib = 90   # observed incident angle middle (should be 90)
    log_output = True         # log the output
    left_mic = 'mic_A'        # which mic is on the left
    frame_length = frame_size / (sampling_rate * 1000)  # sec

    r = Receiver(source, use_file=source_use_file)
    sf = SoundFinder(r, sampling_rate, frame_size, mic_distance, normalize_signal, [filter_lowcut, filter_highcut, filter_order] if filter_on else None, average_delays, left_mic, [angle_middle_calib, angle_edge_calib], log_output, graph_samples)

    # sampling loop
    first = True  # loop control
    while first or repeat:  # run once or forever

        angle = sf.next_angle()  # get next/current angle

        first = False  # loop control

    if graph_samples:
        plt.show()  # for live graph