import numpy as np
import matplotlib.pyplot as plt

# simulated mic settings
mic_delay_a = 0     # ms??
mic_delay_b = 2     # ms??
mic_noise_a = 10    # %
mic_noise_b = 25    # %
print('mic_noise_a: {}%'.format(mic_noise_a))
print('mic_delay_a: {} ms'.format(mic_delay_a))
print('mic_noise_b: {}%'.format(mic_noise_b))
print('mic_delay_b: {} ms'.format(mic_delay_b))

# simulated frequency settings
sin_freq = 440          # Hz or cycles/sec
sampling_rate = 48      # kHz or samples/sec
frame_size = 512        # # samples
frame_length = frame_size / (sampling_rate * 1000)  # ms
print('sin_freq: {} Hz'.format(sin_freq))
print('sampling_rate: {} kHz'.format(sampling_rate))
print('frame_size: {} samples'.format(frame_size))
print('frame_length: {} ms'.format(round(frame_length, 3)))

# generate signal array, add noise & delay
t = np.arange(frame_size)
y = np.sin(2 * np.pi * sin_freq * t / (sampling_rate * 1000))
y_a = np.roll(y + np.random.normal(0, mic_noise_a / 100, y.shape), mic_delay_a)
y_b = np.roll(y + np.random.normal(0, mic_noise_b / 100, y.shape), mic_delay_b)

# plot signals
plt.plot(t, y_a, color='r', label='mic A (noise {}%, delay {} ms)'.format(mic_noise_a, mic_delay_a))
plt.plot(t, y_b, color='g', label='mic B (noise {}%, delay {} ms)'.format(mic_noise_b, mic_delay_b))
plt.xlabel('sample # (t)')
plt.ylabel('delay(sin(x) + noise)')
plt.axis('tight')
plt.legend()
plt.show()