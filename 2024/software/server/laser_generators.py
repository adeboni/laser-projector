import numpy as np
from laser_point import *

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
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(200 * np.sin(d * np.pi / 180) + 2048)
        y = int(200 * np.cos(d * np.pi / 180) + 2048)
        rgb = [0, 0, 255]
        yield [LaserPoint(i, x, y, *rgb) for i in range(num_lasers)]
        d = (d + 8) % 360
