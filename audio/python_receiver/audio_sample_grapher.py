import math
import time
import numpy as np
import matplotlib.pyplot as plt

# sampling settings
source_use_file = False
source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "sample_gen_example1_24kHz_800Hz_0.0003ms.txt"
sampling_rate = 32        # kHz
frame_size = 1024          # #samples
graph_samples = True     # graph on or off
normalize_signal = False  # normalize before graphing
repeat = True             # sample forever or only once
frame_length = frame_size / (sampling_rate * 1000)  # sec

# serial dataframe receiver
from receiver import Receiver
r = Receiver(source, use_file=source_use_file)

# fields
frames_seen = 0             # counter of # frames received
last_frame_ts = 0           # timestamp (ms) of last frame encountered
frame_ts_diff = []          # time differences (ms) between frames
frame_ts_diff_avg_lim = 50  # rolling average of time differences (limit)
frame_period = 0            # time (ms) it takes to get each next frame
frame_freq = 0              # frequency (Hz) of receiving frames

# sampling loop
first = True  # loop control
while first or repeat:  # run once or forever

    # receive 1 data frame
    data = r.receive(frame_size)
    frames_seen += 1
    now_ts = round(time.time() * 1000)
    frame_period = (now_ts - last_frame_ts)
    last_frame_ts = now_ts
    if frames_seen > 1:
        frame_ts_diff.append(frame_period)
        if len(frame_ts_diff) > frame_ts_diff_avg_lim:
            frame_ts_diff = frame_ts_diff[1:]
        frame_period = np.mean(frame_ts_diff)
        frame_freq = 1000 / frame_period
        print("Frame #{}: {}Hz {}ms".format(frames_seen, round(frame_freq, 3), round(frame_period, 3)))
        # print(data)


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

    # output relevant data


    # graph signal alongside correlation if chosen
    if graph_samples:
        plt.cla()
        plt.ylabel("Sample Value")
        plt.xlabel("Sample #")
        plt.plot(x, y_a, color='red')
        plt.plot(x, y_b, color='blue')
        plt.pause(0.001)

    first = False  # loop control

if graph_samples:
    plt.show()  # for live graph
