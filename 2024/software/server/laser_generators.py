import numpy as np
from laser_point import *
from laser_objects import *

def verify_points(points: list[LaserPoint]) -> list[LaserPoint]:
    """Constrains point values to valid ranges"""
    for p in points:
        p.x = min(max(p.x, 0), 4095)
        p.y = min(max(p.y, 0), 4095)
        p.r = min(max(p.r, 0), 255)
        p.g = min(max(p.g, 0), 255)
        p.b = min(max(p.b, 0), 255)
    return points

def interpolate_objects(obj: list[int], seg_dist: int=50) -> list[int]:
    """Converts line segments longer than seg_dist into multiple segments"""
    result = []
    for i in range(1, len(obj)):
        num_segments = max(abs(obj[i-1][0] - obj[i][0]) // seg_dist, abs(obj[i-1][1] - obj[i][1]) // seg_dist) + 2
        x_interp = np.linspace(obj[i-1][0], obj[i][0], num_segments)
        y_interp = np.linspace(obj[i-1][1], obj[i][1], num_segments)
        for x, y in zip(x_interp[:-1], y_interp[:-1]):
            result.append([int(x), int(y), obj[i][2]])
    result.append([obj[i][0], obj[i][1], obj[i][2]])
    return result

def rainbow_circle(num_lasers: int) -> list[LaserPoint]:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(400 * np.sin(d * np.pi / 180) + 2048)
        y = int(400 * np.cos(d * np.pi / 180) + 2048)
        rgb = [d % 255, (d + 60) % 255, (d + 120) % 255]
        yield verify_points([LaserPoint(i, x, y, *rgb) for i in range(num_lasers)])
        d = (d + 8) % 360

def circle(num_lasers: int) -> list[LaserPoint]:
    """Generates a blue circle"""
    d = 0
    while True:
        x = int(200 * np.sin(d * np.pi / 180) + 2048)
        y = int(200 * np.cos(d * np.pi / 180) + 2048)
        rgb = [0, 0, 255]
        yield verify_points([LaserPoint(i, x, y, *rgb) for i in range(num_lasers)])
        d = (d + 8) % 360

def letters(num_lasers: int) -> list[LaserPoint]:
    """Generates A, B, C on three lasers"""
    chars = [interpolate_objects(convert_to_xy(CHAR_A, 2048, 2048)), 
             interpolate_objects(convert_to_xy(CHAR_B, 2048, 2048)), 
             interpolate_objects(convert_to_xy(CHAR_C, 2048, 2048))]
    idxs = [0, 0, 0]
    while True:
        output = []
        for i in range(num_lasers):
            if i >= len(chars):
                continue
            x, y, on = chars[i][idxs[i]]
            idxs[i] = (idxs[i] + 1) % len(chars[i])
            output.append(LaserPoint(i, x, y, 255 * on, 0, 0))
        yield verify_points(output)

def images(num_lasers: int) -> list[LaserPoint]:
    """Generates bike, plane, island on three lasers"""
    imgs = [interpolate_objects(convert_to_xy(IMG_BIKE, 2048, 2048)), 
             interpolate_objects(convert_to_xy(IMG_PLANE, 2048, 2048)), 
             interpolate_objects(convert_to_xy(IMG_ISLAND, 2048, 2048))]
    idxs = [0, 0, 0]
    while True:
        output = []
        for i in range(num_lasers):
            if i >= len(imgs):
                continue
            x, y, on = imgs[i][idxs[i]]
            idxs[i] = (idxs[i] + 1) % len(imgs[i])
            output.append(LaserPoint(i, x, y, 255 * on, 0, 0))
        yield verify_points(output)
