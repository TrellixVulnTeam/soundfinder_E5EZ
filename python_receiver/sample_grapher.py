import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from receiver import Receiver

source_use_file = False
source = "/dev/cu.SLAB_USBtoUART" if not source_use_file else "sample_gen_example1_24kHz_800Hz_0.0003ms.txt"
sampling_rate = 32      # kHz
frame_size = 1024       # #samples
speed_sound = 343       # 343 m/sec = speed of sound in air
mic_distance = 260      # mm
repeat = True
frame_length = frame_size / (sampling_rate * 1000)  # sec

r = Receiver(source, use_file=source_use_file)

first = True
while first or repeat:
    data = r.receive(frame_size)

    N = frame_size
    T = 1/(sampling_rate * 1000)
    x = np.linspace(0, N*T, N)
    y_a = data[:,0]
    y_b = data[:,1]

    plt.cla()
    plt.ylabel("Sample Value")
    plt.xlabel("Sample #")
    plt.plot(x, y_a, color='red')
    plt.plot(x, y_b, color='blue')
    plt.pause(0.001)

    first = False

plt.show()
