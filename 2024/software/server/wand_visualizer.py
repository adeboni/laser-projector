"""This module simulates the sierpinski pyramid"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
import wand
import pygame

wands = []

kano_handler = wand.KanoHandler()
wands.extend(kano_handler.scan())

pygame.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for joystick in joysticks:
    if joystick.get_numaxes() >= 8:
        wands.append(wand.Wand(joystick, pump=True))
    else:
        joystick.quit()

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
    startpoints = -endpoints * 0

    def animate(_):
        q = wands[0].update_position()
        for line, start, end in zip(lines, startpoints, endpoints):
            start = q.rotate(start)
            end = q.rotate(end)
            line.set_data([start[0], end[0]], [start[1], end[1]])
            line.set_3d_properties([start[2], end[2]])

    ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
    plt.show()
