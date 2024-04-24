"""This module visualizes wand positions in 3D"""

import sys
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import pygame
import pyquaternion

wand_type = int(sys.argv[1]) if len(sys.argv) > 1 else None

wands = []

if wand_type is None or wand_type == 1:
    print('Looking for KanoWand()')
    kano_handler = wand.KanoHandler()
    wands.extend(kano_handler.scan())
    if len(wands) > 0:
        wand_type = 1

if wand_type is None or wand_type == 2:
    print('Looking for Wand()')
    pygame.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        if joystick.get_numaxes() >= 8:
            wands.append(wand.Wand(joystick, pump=True))
        else:
            joystick.quit()
    if len(wands) > 0:
        wand_type = 2

print('Found wands:', [wand for wand in wands])

if len(wands) > 0:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim((-5, 5))
    ax.set_ylim((-5, 5))
    ax.set_zlim((-5, 5))
    ax.view_init(20, 50)

    lines = sum([ax.plot([], [], [], c=c) for c in ['r', 'g', 'b']], [])
    wand_graphic_scale = 2
    endpoints = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) * wand_graphic_scale

    wands[0].update_position()

    if wand_type == 1:
        base1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        base2 = pyquaternion.Quaternion(w=1, x=1, y=0, z=0)
        q_init = base2.rotate(base1.rotate(wands[0].position_raw)).inverse
    elif wand_type == 2:
        base1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        base2 = pyquaternion.Quaternion(w=1, x=1, y=0, z=0)
        q_init = base2.rotate(base1.rotate(wands[0].position_raw)).inverse

    def animate(_):
        wands[0].update_position()
        if wand_type == 1:
            q = q_init * base2.rotate(base1.rotate(wands[0].position_raw))
        elif wand_type == 2:
            q = q_init * base2.rotate(base1.rotate(wands[0].position_raw))
        for line, end in zip(lines, endpoints):
            end = q.rotate(end)
            line.set_data([0, end[0]], [0, end[1]])
            line.set_3d_properties([0, end[2]])

    ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
    plt.show()
