import math
import numpy as np
import matplotlib.pyplot as plt

sampling_rate = 32      # kHz --> fake sampling rate of 2000 Hz or 8000 Hz
# frame_size = 1024       # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 250      # mm
graph_relation = True
angle_difference_sample_threshold = 1.0
angle_difference_range_options = [2, 5, 10, 20]
# frame_length = frame_size / (sampling_rate * 1000)  # ms

theta = np.linspace(0, 90, 91)
sample_delay = np.linspace(0, 90, 91)
time_delay = np.linspace(0, 90, 91)

for t in range(len(theta)):
    time_delay[t] = math.cos((math.pi / 180.0) * theta[t]) * (mic_distance / 1000) / speed_sound
    sample_delay[t] = (sampling_rate * 1000) * time_delay[t]
    # time_delay[t] = 0.1 * theta[t] / (57.29578*0.000001*343)
    # sample_delay[t] = time_delay[t]

angle_differences = {}
for r in angle_difference_range_options:
    angle_differences[r] = {}
    for d in range(0,90,r):
        range_end_idx = d + r
        if range_end_idx >= len(sample_delay):
            range_end_idx = len(sample_delay) - 1
        angle_diff = sample_delay[d] - sample_delay[range_end_idx]
        if angle_diff >= angle_difference_sample_threshold:
            angle_differences[r][d] = angle_diff
for r in angle_differences:
    range_label = "{} degrees".format(r)
    print(range_label)
    count = 0
    for d in angle_differences[r]:
        count += 1
        range_end_idx = d + r
        if range_end_idx >= len(sample_delay):
            range_end_idx = len(sample_delay) - 1
        subrange_label = '{}-{}'.format(d, range_end_idx)
        print('{}: {}'.format(subrange_label, round(angle_differences[r][d], 3)))
    if count == 0:
        print("no differences over {} samples".format(angle_difference_sample_threshold))
    print("")

if graph_relation:
    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Theta")
    ax1.set_ylabel("Sample Delay", color='red')
    ax1.plot(theta, sample_delay, color='red', marker='o')
    ax1.tick_params(axis='y', labelcolor='red')
    ax2 = ax1.twinx()
    ax2.set_ylabel("Time Delay", color='blue')
    ax2.plot(theta, time_delay, color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    fig.tight_layout()

    fig.savefig('angle_delay_relation_{}kHz_{}mm.png'.format(sampling_rate, mic_distance))
    plt.show()