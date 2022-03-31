import numpy as np
import matplotlib.pyplot as plt
x = np.linspace(-np.pi, np.pi, 10)
y = np.sin(x)
plt.plot(x, y)
plt.xlabel('Angle in radians')
plt.ylabel('sin(x)')
plt.axis('tight')
plt.show()