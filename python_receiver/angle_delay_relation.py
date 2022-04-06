import math
import numpy as np
import matplotlib.pyplot as plt

sampling_rate = 48      # kHz --> fake sampling rate of 2000 Hz or 8000 Hz
frame_size = 192        # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 250      # mm
frame_length = frame_size / (sampling_rate * 1000)  # ms

theta = np.linspace(0, 90, 91)
sample_delay = np.linspace(0, 90, 91)
time_delay = np.linspace(0, 90, 91)

for t in range(len(theta)):
    time_delay[t] = math.cos((math.pi / 180.0) * theta[t]) * (mic_distance / 1000) / speed_sound
    sample_delay[t] = (sampling_rate * 1000) * time_delay[t]
    # time_delay[t] = 0.1 * theta[t] / (57.29578*0.000001*343)
    # sample_delay[t] = time_delay[t]

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
plt.show()