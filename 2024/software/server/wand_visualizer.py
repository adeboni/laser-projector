"""This module visualizes wand positions in 3D"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import pygame
import sierpinski

wands = []

kano_handler = wand.KanoScanner()
wands.extend(kano_handler.scan())

pygame.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for joystick in joysticks:
    if joystick.get_numaxes() >= 8:
        wands.append(wand.Wand(joystick, pump=True))
    else:
        joystick.quit()

if len(wands) == 0:
    wands.append(wand.WandSimulator())

print('Found wands:', [wand for wand in wands])

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

def animate(_):
    wands[0].update_position()
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
