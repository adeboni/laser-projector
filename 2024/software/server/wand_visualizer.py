"""This module visualizes wand positions in 3D"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import pygame
import sierpinski
import pyquaternion
import time

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
    wands.append(wand.WandSimulatorQuat())

print('Found wands:', [wand for wand in wands])

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim((-2, 2))
ax.set_ylim((-2, 2))
ax.set_zlim((-2, 2))
ax.view_init(20, 50)

lines = sum([ax.plot([], [], [], c=c) for c in ['k', 'r', 'g', 'b']], [])
endpoints = np.array([sierpinski.target_vector, [1, 0, 0], [0, 1, 0], [0, 0, 1]])

def quaternion_between_vectors(v1, v2):
    w = np.sqrt((np.linalg.norm(v1)**2) * (np.linalg.norm(v2)**2)) + np.dot(v1, v2)
    x, y, z = np.cross(v1, v2)
    q = np.array([w, x, y, z]) / np.linalg.norm([w, x, y, z])
    return pyquaternion.Quaternion(w=q[0], x=q[1], y=q[2], z=q[3])

q_init = quaternion_between_vectors(endpoints[1], endpoints[0])

def euler_angles_between_vectors(v1, v2):
    dot = np.dot(v1, v2)
    cross = np.cross(v1, v2)
    yaw = np.arctan2(cross[1], cross[0])
    pitch = np.arctan2(cross[2], np.sqrt(cross[0]**2 + cross[1]**2))
    roll = np.arctan2(dot, np.sqrt(1 - dot**2))
    return (np.degrees(yaw), np.degrees(pitch), np.degrees(roll))

next_print = 0

def animate(_):
    global next_print
    wands[0].update_position()
    q = wands[0].position
    for i, (line, end) in enumerate(zip(lines, endpoints)):
        new_end = q.rotate(end)
        line.set_data([0, new_end[0]], [0, new_end[1]])
        line.set_3d_properties([0, new_end[2]])
        if time.time() > next_print and i == 1:
            print(f'{end} -> {new_end} = {euler_angles_between_vectors(end, new_end)}')
            next_print = time.time() + 0.25

ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
plt.show()
