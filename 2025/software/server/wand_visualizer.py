"""This module visualizes wand positions in 3D"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import sierpinski
import time

found_wand = None
use_wifi = True

if use_wifi:
    ws = wand.WandServer()
    ws.start_udp()
    start_time = time.time()
    while time.time() - start_time < 5:
        connected_wands = ws.get_connected_wands()
        if len(connected_wands) > 0:
            found_wand = connected_wands[0]
            break

if found_wand is None:
    found_wand = wand.WandSimulator()

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

found_wand.impact_callback = lambda: print('Hit')


def get_euler_angles(w, x, y, z):
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    rotation = np.arctan2(t0, t1)
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, a_min=-1.0, a_max=1.0)
    pitch = np.arcsin(t2)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)
    print((rotation, pitch, yaw))


def animate(_):
    q = found_wand.position
    #get_euler_angles(q[0], q[1], q[2], q[3])
    for line, end in zip(lines, endpoints):
        v = q.rotate(end)
        line.set_data([0, v[0]], [0, v[1]])
        line.set_3d_properties([0, v[2]])
    v = sierpinski.apply_quaternion(q)
    target_line[0].set_data([0, v[0]], [0, v[1]])
    target_line[0].set_3d_properties([0, v[2]])

ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
plt.show()
