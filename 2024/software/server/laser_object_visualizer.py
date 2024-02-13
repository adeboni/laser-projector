import math
from matplotlib import pyplot as plt
from laser_point import *
from laser_objects import *

graphic_raw = CHAR_A

grid_size = int(math.sqrt(len(graphic_raw) // 2)) + 1

fig = plt.figure()
axs = [fig.add_subplot(grid_size, grid_size, i + 1) for i in range(len(graphic_raw) // 2)]

x = []
y = []
c = []

for i in range(0, len(graphic_raw), 2):
    x.append((graphic_raw[i] & 0x7FFF) + 2048)
    y.append(graphic_raw[i+1] + 2048)
    c.append('r' if graphic_raw[i] & 0x8000 else 'k')
    axs[i // 2].set_xlim([0, 4095])
    axs[i // 2].set_ylim([0, 4095])
    axs[i // 2].set_aspect('equal')
    axs[i // 2].set_title(f'Step {i // 2 + 1}')
    for xx, yy, cc in zip(x, y, c):
        axs[i // 2].plot([xx], [yy], c=cc, linestyle='', marker='o')
    for j in range(1, len(x)):
        axs[i // 2].plot([x[j - 1], x[j]], [y[j - 1], y[j]], c=c[j])

plt.show()
