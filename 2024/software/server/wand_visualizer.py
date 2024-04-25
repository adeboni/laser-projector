"""This module visualizes wand positions in 3D"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import pygame
import sierpinski
import pyquaternion

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

print('Found wands:', [wand for wand in wands])
if len(wands) == 0:
    quit()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim((-5, 5))
ax.set_ylim((-5, 5))
ax.set_zlim((-5, 5))
ax.view_init(20, 50)

lines = sum([ax.plot([], [], [], c=c) for c in ['k', 'r', 'g', 'b']], [])
wand_graphic_scale = 2
endpoints = np.array([sierpinski.target_vector, [1, 0, 0], [0, 1, 0], [0, 0, 1]]) * wand_graphic_scale

def quaternion_between_vectors(v1, v2):
    v1 = v1 / np.linalg.norm(v1)
    v2 = v2 / np.linalg.norm(v2)
    w = np.sqrt((np.linalg.norm(v1)**2) * (np.linalg.norm(v2)**2)) + np.dot(v1, v2)
    x, y, z = np.cross(v1, v2)
    q = np.array([w, x, y, z]) / np.linalg.norm([w, x, y, z])
    return pyquaternion.Quaternion(w=q[0], x=q[1], y=q[2], z=q[3])

q_init = quaternion_between_vectors(endpoints[1], endpoints[0])

def animate(_):
    wands[0].update_position()
    #q = q_init * wands[0].position
    q = wands[0].position
    for line, end in zip(lines, endpoints):
        end = q.rotate(end)
        line.set_data([0, end[0]], [0, end[1]])
        line.set_3d_properties([0, end[2]])

ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
plt.show()
