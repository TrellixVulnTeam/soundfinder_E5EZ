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
        self.sampling_rate = sampling_rate                                      # kHz  -  MUST MATCH ESP              (ideal = 16 or 32)
        self.frame_size = frame_size                                            # #samples  -  MUST MATCH ESP         (ideal = 512 or 1024)
        self.frame_length = frame_size / (sampling_rate * 1000)                 # sec
        self.mic_distance = mic_distance                                        # mm  -  MUST MATCH SETUP             (ideal = 75mm, 250mm, 500mm, 1000mm)
        self.filter_on = not(filter_bounds == None or filter_bounds == False)   # butterworth bandpass filter         (ideal = True)
        self.filter_lowcut = filter_bounds[0] if filter_bounds else 0.0         # Hz                                  (ideal = 400-500)
        self.filter_highcut = filter_bounds[1] if filter_bounds else 2000.0     # Hz                                  (ideal = 1200-1400)
        self.filter_order = filter_bounds[2] if filter_bounds else 1            # filter order                        (ideal = 4 for filtfilt, 8 for sosfiltfilt)
        self.filter_ratio = filter_bounds[3] if filter_bounds else 20           # %                                   (ideal = 20-25)
        self.filter_bands = filter_bounds[4] if filter_bounds and filter_bounds[4] else []
        self.filter_bands_avg_ratio = filter_bounds[6] if filter_bounds else 10
        self.filter_bands_order = filter_bounds[7] if filter_bounds else self.filter_order
        self.average_delays = average_delays                                    # rolling average on sample delay (0 for none) (ideal = 3 --> for more stability in values as well as smoother range)
        self.graph_samples = graph_samples                                      # generate plot (takes more time)
        self.graph_filtered = filter_bounds[5] if filter_bounds else False
        self.angle_edge_calib = angle_calibration[1]                            # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45) (ideal = 25)
        self.angle_middle_calib = angle_calibration[0]                          # observed incident angle middle (should be 90)
        self.normalize_signal = normalize_sig                                   # normalize before correlation        (ideal = True)
        self.left_mic = left_mic
        # instance fields
        self.r = receiver                               # serial dataframe receiver (import from receiver.py)
        self.speed_sound = 343                          # 343 m/sec = speed of sound in air
        self.frame_counter = 0                          # frame counter
        self.incident_angle = 90                        # initial value
        self.lag_sample_delay_rolling_avg = []          # rolling avg array
        self.log_output = log_output
        self.time_delay_filter_update_thres = 0.0006250  # sec --> 0.0003125sec converts to 5 samples with 16kHz & 1024
        self.sample_delay_filter_update_thres = self.time_delay_filter_update_thres * self.frame_size / self.frame_length
        # output values
        self.data = None                                # current/last signal data frame
        self.lag_time_delay = 0
        self.lag_sample_delay = 0
        self.lag_sample_delay_filt = 0
        self.lag_sample_delay_raw = 0
        self.lag_sample_delay_bands = [0 for i in range(len(self.filter_bands))]
        self.lag_time_delay_bands = [0 for i in range(len(self.filter_bands))]
        self.freq_band_incident_angles = [90 for i in range(len(self.filter_bands))]
        self.freq_band_incident_mics = ['both' for i in range(len(self.filter_bands))]
        # self.lag_time_delay_filt = 0
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

    # utility method to switch from TDOA incident angle coordinate system to camera's coordinate system
    def convert_angle(self, angle, mic):
        angle_invert = 90 - angle
        if not (mic == self.left_mic):
            angle_invert *= -1
        return angle_invert

    # filter utility functions
    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        # sos = scipy.signal.butter(order, [low, high], analog=False, btype='band', output='sos')
        # return sos
        b, a = scipy.signal.butter(order, [low, high], analog=False, btype='band')
        return (b, a)
    def butter_bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        # sos = self.butter_bandpass(lowcut, highcut, fs, order=order)
        # y = scipy.signal.sosfiltfilt(sos, data)
        # y = scipy.signal.sosfilt(sos, data)
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        y = scipy.signal.filtfilt(b, a, data)
        # y = scipy.signal.lfilt(b, a, data)
        return y

    # get next/current angle and incident mic
    def next_angle(self):

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
            y_a_div = np.std(y_a)
            y_b_div = np.std(y_a)
            y_a_div = y_a_div if y_a_div != 0 else 1
            y_b_div = y_b_div if y_b_div != 0 else 1
            y_a = (y_a - np.mean(y_a)) / y_a_div
            y_b = (y_b - np.mean(y_b)) / y_b_div
        # filter signal data if chosen
        y_a_filt = None
        y_b_filt = None
        if self.filter_on:
            y_a_filt = self.butter_bandpass_filter(y_a, self.filter_lowcut, self.filter_highcut, self.sampling_rate * 1000, order=self.filter_order)
            y_b_filt = self.butter_bandpass_filter(y_b, self.filter_lowcut, self.filter_highcut, self.sampling_rate * 1000, order=self.filter_order)

        # perform fft
        yf_a = scipy.fftpack.fft(y_a_filt if self.filter_on else y_a)
        yf_b = scipy.fftpack.fft(y_b_filt if self.filter_on else y_b)
        xf = np.linspace(0, 1//(2*T), N//2)

        # correlate signals & calculate signal lag
        yc = scipy.signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
        # extract sample delay from correlation graph
        self.lag_sample_delay_raw = yc.argmax() - (len(y_a) - 1)
        # compare to filtered correlation to confirm angle change
        filter_angle_update = not self.filter_on
        if self.filter_on:
            yc_filt = scipy.signal.correlate(y_a_filt - np.mean(y_a_filt), y_b_filt - np.mean(y_b_filt), mode='full')
            self.lag_sample_delay_filt = yc_filt.argmax() - (len(y_a_filt) - 1)
            if abs(self.lag_sample_delay_raw - self.lag_sample_delay_filt) <= self.sample_delay_filter_update_thres:
                self.lag_sample_delay = round(((self.filter_ratio / 100) * self.lag_sample_delay_filt) + ((1 - (self.filter_ratio / 100)) * self.lag_sample_delay_raw))
                filter_angle_update = True
            #     print('UPDATE')
            # print(self.lag_sample_delay_raw)
            # print(self.lag_sample_delay_filt)
            # print('')
        else:
            self.lag_sample_delay = self.lag_sample_delay_raw

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

        # calculate sound source angle of arrival using time delay, speed of sound, and mic distance
        new_incident_angle = 90
        try:  # try-catch needed for arccos domain errors (probably noisy outlier delay values whose source angle would be out of range/impossible)
            new_incident_angle = (180.0 / math.pi) * math.acos(self.speed_sound * (self.lag_time_delay) / (self.mic_distance / 1000))
        except:
            new_incident_angle = self.incident_angle
        self.incident_angle = new_incident_angle
        # determine which mic the sound hit first
        self.incident_mic = 'both' if self.lag_sample_delay == 0 or new_incident_angle == 90 else ('mic_A' if self.lag_sample_delay < 0 else 'mic_B')


        # experiment with multiple filters
        if self.filter_bands != None and len(self.filter_bands) > 0:
            y_a_bands = [None for i in range(len(self.filter_bands))]
            y_b_bands = [None for i in range(len(self.filter_bands))]
            for b in range(len(self.filter_bands)):
                f_lc = self.filter_bands[b][0]
                f_hc = self.filter_bands[b][1]
                f_o = self.filter_bands_order
                y_a_bands[b] = self.butter_bandpass_filter(y_a, f_lc, f_hc, self.sampling_rate * 1000, order=f_o)
                y_b_bands[b] = self.butter_bandpass_filter(y_b, f_lc, f_hc, self.sampling_rate * 1000, order=f_o)
                yc_band_b = scipy.signal.correlate(y_a_bands[b] - np.mean(y_a_bands[b]), y_b_bands[b] - np.mean(y_b_bands[b]), mode='full')
                self.lag_sample_delay_bands[b] = yc_band_b.argmax() - (len(y_a_bands[b]) - 1)
                self.lag_time_delay_bands[b] = abs(self.lag_sample_delay_bands[b]) * self.frame_length / self.frame_size
                new_incident_angle_band_b = 90
                try:
                    new_incident_angle_band_b = (180.0 / math.pi) * math.acos(self.speed_sound * (self.lag_time_delay_bands[b]) / (self.mic_distance / 1000))
                except:
                    new_incident_angle_band_b = self.freq_band_incident_angles[b]
                self.freq_band_incident_angles[b] = new_incident_angle_band_b
                self.freq_band_incident_mics[b] = 'both' if self.lag_sample_delay_bands[b] == 0 or new_incident_angle_band_b == 90 else ('mic_A' if self.lag_sample_delay_bands[b] < 0 else 'mic_B')
            band_avg_angle = np.mean(self.freq_band_incident_angles)
            both_c = 0
            mic_a_c = 0
            mic_b_c = 0
            avg_incident_mic = 'both'
            for mic in self.freq_band_incident_mics:
                if mic == 'both':
                    both_c += 1
                elif mic == 'mic_A':
                    mic_a_c += 1
                elif mic == 'mic_B':
                    mic_b_c += 1
            if both_c > mic_a_c and both_c > mic_b_c:
                avg_incident_mic = 'both'
            elif mic_a_c > both_c and mic_a_c > mic_b_c:
                avg_incident_mic = 'mic_A'
            elif mic_b_c > both_c and mic_b_c > mic_a_c:   
                avg_incident_mic = 'mic_B'
            # only fine-tune the angle if the filter bands avg incident mic is the same as the unfiltered incident mic AND the filtered correlation agrees with the unfiltered correlation
            if ((not self.filter_on) or filter_angle_update) and avg_incident_mic == self.incident_mic:
            # if avg_incident_mic == self.incident_mic:
                # old_incident_angle = self.incident_angle
                self.incident_angle = ((1 - (filter_bands_avg_ratio / 100)) * self.incident_angle) + ((filter_bands_avg_ratio / 100) * band_avg_angle)
                # print('{} --> {} :({})'.format(round(old_incident_angle, 2), round(self.incident_angle, 2), round(band_avg_angle, 2)))

        # fine-tune value with calibration incident angle edge (extrapolate range)
        self.fine_tuned_incident_angle = self.incident_angle
        if self.angle_edge_calib != 0:
            angle_val = self.incident_angle
            if angle_val < self.angle_edge_calib:
                angle_val = self.angle_edge_calib
            self.fine_tuned_incident_angle = self.angle_middle_calib - (self.angle_middle_calib * ((self.angle_middle_calib - angle_val) / (self.angle_middle_calib - self.angle_edge_calib)))

        # output relevant data
        if self.log_output:
            if filter_angle_update:
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
            self.ax1.plot(x, y_a_filt if self.filter_on and self.graph_filtered else y_a, color='red')
            self.ax1.plot(x, y_b_filt if self.filter_on and self.graph_filtered else y_b, color='blue')
            # self.ax1.plot(x, y_a_bands[1], color='red')
            # self.ax1.plot(x, y_b_bands[1], color='blue')
            # graph correlation
            self.ax2.cla()
            self.ax2.set_title("Correlation: {} @ {}°".format('left' if self.incident_mic == self.left_mic else 'right', round(self.fine_tuned_incident_angle, 3)))
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



# entry point
if __name__ == "__main__":

    # sampling & correlation settings
    source_use_file = False   # use device or file
    source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "data/sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
    sampling_rate = 16        # kHz  -  MUST MATCH ESP              (ideal = 16 or 32)
    frame_size = 512          # #samples  -  MUST MATCH ESP         (ideal = 512 or 1024)
    mic_distance = 250        # mm  -  MUST MATCH SETUP             (ideal = 75mm, 250mm, 500mm, 1000mm)
    average_delays = 3        # rolling average on sample delay (0 for none) (ideal = 3 --> for more stability in values as well as smoother range)
    normalize_signal = True   # normalize before correlation        (ideal = True)
    filter_on = True          # butterworth bandpass filter         (ideal = True)
    filter_lowcut = 500.0     # Hz                                  (ideal = 400-500)
    filter_highcut = 1200.0   # Hz                                  (ideal = 1200-1400)
    filter_order = 4          # filter order                        (ideal = 4 for filtfilt, 8 for sosfiltfilt)
    filter_ratio = 30         # %                                   (ideal = 20-30)
    filter_bands_order = 6
    # filter_bands = None
    filter_bands = [ [550,750], [650,850], [400,500], [500,600], [600,700], [700,800], [800,900], [900,1000] ]
    filter_bands_avg_ratio = 10 # %                                 (ideal = 15-20)
    filter_graph = False      # display filtered or unfiltered signal frame on graph
    repeat = True             # sample forever or only once
    graph_samples = True      # generate plot (takes more time)
    angle_edge_calib = 25     # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45) (ideal = 25)
    angle_middle_calib = 90   # observed incident angle middle (should be 90)
    log_output = False         # log the output
    left_mic = 'mic_A'        # which mic is on the left  (usually = 'mic_A')
    frame_length = frame_size / (sampling_rate * 1000)  # sec

    # ESP32 serial dataframe receiver
    r = Receiver(source, use_file=source_use_file)
    # sound finding algorithm
    sf = SoundFinder(r, sampling_rate, frame_size, mic_distance, normalize_signal, [filter_lowcut, filter_highcut, filter_order, filter_ratio, filter_bands, filter_graph, filter_bands_avg_ratio, filter_bands_order] if filter_on else None, average_delays, left_mic, [angle_middle_calib, angle_edge_calib], log_output, graph_samples)

    # sampling loop
    first = True  # loop control
    while first or repeat:  # run once or forever

        angle = sf.next_angle()  # get next/current angle

        first = False  # loop control

    if graph_samples:
        plt.show()  # for live graph