import math
import numpy as np
import scipy.signal
import scipy.fftpack
import matplotlib.pyplot as plt

# sampling & correlation settings
source_use_file = False   # use device or file
source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "data/sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
sampling_rate = 32        # kHz  -  MUST MATCH ESP
frame_size = 768          # #samples  -  MUST MATCH ESP
mic_distance = 250        # mm  -  MUST MATCH SETUP
speed_sound = 343         # 343 m/sec = speed of sound in air
average_delays = 5       # rolling average on sample delay (set to 0 for none)
normalize_signal = True   # normalize before correlation
filter_on = True          # butterworth bandpass filter
filter_lowcut = 400.0     # Hz
filter_highcut = 1400.0   # Hz
filter_order = 10         # filter order
repeat = True             # sample forever or only once
graph_samples = True      # generate plot (takes more time)
angle_edge_calib = 25  #25 # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45)
angle_middle_calib = 90   # observed incident angle middle (should be 90)
frame_length = frame_size / (sampling_rate * 1000)  # sec

# serial dataframe receiver
from receiver import Receiver
r = Receiver(source, use_file=source_use_file)

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

# fields
frame_counter = 0
incident_angle = 90  # initial value
lag_sample_delay_rolling_avg = []  # rolling avg array
fig, (ax1, ax2, ax3) = plt.subplots(3, figsize=(8, 7))  # plots for easy/fast redrawing

# sampling loop
first = True  # loop control
while first or repeat:  # run once or forever

    # receive 1 data frame
    data = r.receive(frame_size)
    frame_counter += 1

    # preprocess signal data
    N = frame_size
    T = 1/(sampling_rate * 1000)
    x = np.linspace(0, N*T, N)
    y_a = data[:,0]
    y_b = data[:,1]
    # normalize signal data if chosen
    if normalize_signal:
        y_a = (y_a - np.mean(y_a)) / np.std(y_a)
        y_b = (y_b - np.mean(y_b)) / np.std(y_b)
    # filter signal data if chosen
    if filter_on:
        y_a = butter_bandpass_filter(y_a, filter_lowcut, filter_highcut, sampling_rate * 1000, order=filter_order)
        y_b = butter_bandpass_filter(y_b, filter_lowcut, filter_highcut, sampling_rate * 1000, order=filter_order)

    # perform fft
    yf_a = scipy.fftpack.fft(y_a)
    yf_b = scipy.fftpack.fft(y_b)
    xf = np.linspace(0, 1//(2*T), N//2)

    # correlate signals & calculate signal lag
    yc = scipy.signal.correlate(y_a - np.mean(y_a), y_b - np.mean(y_b), mode='full')
    # extract sample delay from correlation graph
    lag_sample_delay = yc.argmax() - (len(y_a) - 1)
    # rolling average on sample delays if chosen (smooths out outliers/noise)
    if average_delays > 0:
        lag_sample_delay_rolling_avg.append(lag_sample_delay)
        if len(lag_sample_delay_rolling_avg) > average_delays:
            lag_sample_delay_rolling_avg = lag_sample_delay_rolling_avg[1:]
        lag_sample_delay = math.ceil(np.mean(lag_sample_delay_rolling_avg))
    # calculate time delay from sample delay
    lag_time_delay = abs(lag_sample_delay) * frame_length / frame_size
    # generate x-axis (in either sample or time delay) to make sense of correlation graph
    xc = np.linspace((-1 * (len(yc) / 2) - 1), (len(yc) / 2) - 1, len(yc))  # in samples
    xc = xc * frame_length / frame_size    # in sec

    # determine which mic the sound hit first
    incident_mic = 'both' if lag_sample_delay == 0 else ('mic_A' if lag_sample_delay < 0 else 'mic_B')
    # calculate sound source angle of arrival using time delay, speed of sound, and mic distance
    try:  # try-catch needed for arccos domain errors (probably noisy outlier delay values whose source angle would be out of range/impossible)
        new_incident_angle = (180.0 / math.pi) * math.acos(speed_sound * (lag_time_delay) / (mic_distance / 1000))
    except:
        new_incident_angle = incident_angle
    incident_angle = new_incident_angle

    # fine-tune value with calibration incident angle edge
    fine_tuned_incident_angle = incident_angle
    if angle_edge_calib != 0:
        angle_val = incident_angle
        if angle_val < angle_edge_calib:
            angle_val = angle_edge_calib
        fine_tuned_incident_angle = angle_middle_calib - (angle_middle_calib * ((angle_middle_calib - angle_val) / (angle_middle_calib - angle_edge_calib)))

    # output relevant data
    print("{} @ {}deg <-- {}deg <-- d={}ms,{}sam@c{}".format(incident_mic, round(fine_tuned_incident_angle, 3), round(incident_angle, 3), lag_time_delay, lag_sample_delay, round(yc[lag_sample_delay], 3)))
    # print("Sample Delay/Lag: {} samples".format(lag_sample_delay))
    # print("Time Delay/Lag: {} ms".format(lag_time_delay))
    # print("Correlation: {}".format(round(yc[lag_sample_delay], 3)))
    # print("Incident Mic: {}".format(incident_mic))
    # print("Incident Angle: {}deg".format(round(incident_angle, 3)))
    # print("Fine-Tuned Incident Angle: {}deg".format(round(fine_tuned_incident_angle, 3)))
    # print(lag_sample_delay_rolling_avg)

    # graph signal alongside correlation if chosen
    if graph_samples:
        # graph signal
        ax1.cla()
        ax1.set_title("Signal Frame")
        ax1.set_ylabel("Sample Value")
        ax1.set_xlabel("Sample #")
        ax1.plot(x, y_a, color='red')
        ax1.plot(x, y_b, color='blue')
        # graph correlation
        ax2.cla()
        ax2.set_title("Correlation: {} @ {}°".format(incident_mic, round(fine_tuned_incident_angle, 3)))
        ax2.set_ylabel("Correlation")
        ax2.set_xlabel("Delay/Lag")
        ax2.plot(xc, yc)  # marker='o')
        ax2.annotate('argmax={}@{}ms'.format(round(yc[lag_sample_delay], 3), lag_time_delay),  (lag_time_delay, yc[yc.argmax()]), ha='center')
        # graph fft
        ax3.cla()
        ax3.set_title("Fourier Transform")
        ax3.set_ylabel("Amplitude")
        ax3.set_xlabel("Frequency [Hz]")
        ax3.plot(xf, 2/N * np.abs(yf_a[:N//2]))
        ax3.plot(xf, 2/N * np.abs(yf_b[:N//2]))

        fig.tight_layout()
        plt.pause(0.25) # live periodic update
        plt.savefig("./graphs/correlation_output_{}.png".format(frame_counter))

    first = False  # loop control

if graph_samples:
    plt.show()  # for live graph

# plt.savefig('')

