import math
import numpy as np
import matplotlib.pyplot as plt

output_name = 'example1'
# simulated mic settings
mic_delay_a = 0      # ms
mic_delay_b = 0.0010 # ms
mic_noise_a = 15     # %
mic_noise_b = 30     # %
# simulated freq settings
sin_freq = 440          # Hz or cycles/sec
sampling_rate = 8       # kHz or samples/sec
frame_size = 128        # #samples
adc_resolution = 4096   # ADC range/resolution
adc_amp_cutoff = 1896   # amplifier amplitude cutoff
# calculate further settings
frame_length = frame_size / (sampling_rate * 1000)  # ms
mic_sample_delay_a = math.floor((mic_delay_a * frame_size) / frame_length)
mic_sample_delay_b = math.floor((mic_delay_b * frame_size) / frame_length)

# print settings
print('generating samples for "{}"'.format(output_name))
print('sin_freq: {} Hz'.format(sin_freq))
print('sampling_rate: {} kHz'.format(sampling_rate))
print('frame_size: {} samples'.format(frame_size))
print('frame_length: {} ms'.format(round(frame_length, 3)))
print('mic_noise_a: {}%'.format(mic_noise_a))
print('mic_delay_a: {} ms'.format(mic_delay_a))
print('mic_noise_b: {}%'.format(mic_noise_b))
print('mic_delay_b: {} ms'.format(mic_delay_b))
print('mic_sample_delay_a: {}'.format(mic_sample_delay_a))
print('mic_sample_delay_b: {}'.format(mic_sample_delay_b))

# generate signal array, add noise & delay
t = np.arange(frame_size)
y = np.sin(2 * np.pi * sin_freq * t / (sampling_rate * 1000))
y_a = np.roll(y + np.random.normal(0, mic_noise_a / 100, y.shape), mic_sample_delay_a)
y_b = np.roll(y + np.random.normal(0, mic_noise_b / 100, y.shape), mic_sample_delay_b)
y_a = ((adc_resolution - adc_amp_cutoff) * (y_a - np.min(y_a)) / (np.max(y_a) - np.min(y_a))).astype(int)  # normalize
y_b = ((adc_resolution - adc_amp_cutoff) * (y_b - np.min(y_b)) / (np.max(y_b) - np.min(y_b))).astype(int)  # normalize

# save output
line_count = 0
with open('sample_gen_{}_{}kHz_{}Hz_{}ms.txt'.format(output_name, sampling_rate, sin_freq, round(mic_delay_b - mic_delay_a,3)).format(output_name), 'w') as output_file:
    output_file.write('s\n')
    for ti in t:
        output_file.write('{} {} {}\n'.format(ti, y_a[ti], y_b[ti]))
        line_count += 1
print('generated {} samples'.format(line_count))

# plot signals
plt.plot(t, y_a, color='r', label='mic A (noise={}%, delay={}ms or {} samples)'.format(mic_noise_a, mic_delay_a, mic_sample_delay_a))
plt.plot(t, y_b, color='g', label='mic B (noise={}%, delay={}ms or {} samples)'.format(mic_noise_b, mic_delay_b, mic_sample_delay_b))
plt.xlabel('sample # (t)')
plt.ylabel('delay(sin(x) + noise)')
plt.axis('tight')
plt.legend()

plt.savefig('sample_gen_{}_{}kHz_{}Hz_{}ms.png'.format(output_name, sampling_rate, sin_freq, round(mic_delay_b - mic_delay_a,3)))
plt.show()
