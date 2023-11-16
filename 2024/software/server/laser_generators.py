import numpy as np
from laser_point import *

def rainbow_circle() -> LaserPoint:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(1000 * np.sin(d * np.pi / 180) + 2048)
        y = int(1000 * np.cos(d * np.pi / 180) + 2048)
        rgb = [d % 255, (d + 60) % 255, (d + 120) % 255]
        yield LaserPoint(0, x, y, *rgb)
        d = (d + 8) % 360

def circle() -> LaserPoint:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(1000 * np.sin(d * np.pi / 180) + 2048)
        y = int(1000 * np.cos(d * np.pi / 180) + 2048)
        rgb = [0, 0, 255]
        yield LaserPoint(0, x, y, *rgb)
        d = (d + 8) % 360
