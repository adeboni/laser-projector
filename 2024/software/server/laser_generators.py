import numpy as np
from laser_point import *
from laser_objects import *

def rainbow_circle(num_lasers: int) -> list[LaserPoint]:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(400 * np.sin(d * np.pi / 180) + 2048)
        y = int(400 * np.cos(d * np.pi / 180) + 2048)
        rgb = [d % 255, (d + 60) % 255, (d + 120) % 255]
        yield [LaserPoint(i, x, y, *rgb) for i in range(num_lasers)]
        d = (d + 8) % 360

def circle(num_lasers: int) -> list[LaserPoint]:
    """Generates a blue circle"""
    d = 0
    while True:
        x = int(200 * np.sin(d * np.pi / 180) + 2048)
        y = int(200 * np.cos(d * np.pi / 180) + 2048)
        rgb = [0, 0, 255]
        yield [LaserPoint(i, x, y, *rgb) for i in range(num_lasers)]
        d = (d + 8) % 360

def letters(num_lasers: int) -> list[LaserPoint]:
    """Generates A, B, C on three lasers"""
    chars = [convert_to_xy(CHAR_A, 2048, 2048), 
             convert_to_xy(CHAR_B, 2048, 2048), 
             convert_to_xy(CHAR_C, 2048, 2048)]
    idxs = [0, 0, 0]
    while True:
        output = []
        for i in range(num_lasers):
            if i >= len(chars):
                continue
            x, y, on = chars[i][idxs[i]]
            idxs[i] = (idxs[i] + 1) % len(chars[i])
            output.append(LaserPoint(i, x, y, 255 * on, 0, 0))
        yield output

    