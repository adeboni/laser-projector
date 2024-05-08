"""This module visualizes wand positions in 3D"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import sierpinski

ble_scanner = wand.BLEScanner()
wands = ble_scanner.scan()
if len(wands) == 0:
    wands.append(wand.WandSimulator())

print('Found wands:', wands)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim((-2, 2))
ax.set_ylim((-2, 2))
ax.set_zlim((-2, 2))
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.view_init(20, 50)

target_line = ax.plot([], [], [], c='k')
lines = sum([ax.plot([], [], [], c=c) for c in ['r', 'g', 'b']], [])
endpoints = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

wands[0].callback = lambda: print('Hit')

def animate(_):
    q = wands[0].position
    for line, end in zip(lines, endpoints):
        v = q.rotate(end)
        line.set_data([0, v[0]], [0, v[1]])
        line.set_3d_properties([0, v[2]])
    v = sierpinski.apply_quaternion(q)
    target_line[0].set_data([0, v[0]], [0, v[1]])
    target_line[0].set_3d_properties([0, v[2]])

ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
plt.show()
