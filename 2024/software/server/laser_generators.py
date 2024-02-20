import numpy as np
from laser_point import *
from laser_objects import *
from typing import Generator
import sierpinski

def verify_points(points: list[LaserPoint]) -> list[LaserPoint]:
    """Constrains point values to valid ranges"""
    for p in points:
        p.x = min(max(p.x, 0), 4095)
        p.y = min(max(p.y, 0), 4095)
        p.r = min(max(p.r, 0), 255)
        p.g = min(max(p.g, 0), 255)
        p.b = min(max(p.b, 0), 255)
    return points

def interpolate_objects(obj: list[int], seg_dist: int=32) -> list[int]:
    """Converts line segments longer than seg_dist into multiple segments"""
    result = [[obj[0][0], obj[0][1], obj[0][2]]]
    for i in range(1, len(obj)):
        num_segments = max(abs(obj[i-1][0] - obj[i][0]) // seg_dist, abs(obj[i-1][1] - obj[i][1]) // seg_dist) + 2
        x_interp = np.linspace(obj[i-1][0], obj[i][0], num_segments)
        y_interp = np.linspace(obj[i-1][1], obj[i][1], num_segments)
        for x, y in zip(x_interp[1:], y_interp[1:]):
            result.append([int(x), int(y), obj[i][2]])
    return result

def rainbow_circle(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = int(400 * np.sin(d * np.pi / 180) + 2048)
        y = int(400 * np.cos(d * np.pi / 180) + 2048)
        rgb = [d % 255, (d + 60) % 255, (d + 120) % 255]
        yield verify_points([LaserPoint(i, x, y, *rgb) for i in range(num_lasers)])
        d = (d + 8) % 360

def circle(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates an rgb circle"""
    d = 0
    while True:
        x = int(200 * np.sin(d * np.pi / 180) + 2048)
        y = int(200 * np.cos(d * np.pi / 180) + 2048)
        rgb = [255 if d < 120 else 0, 255 if 120 <= d <= 240 else 0, 255 if d > 240 else 0]
        yield verify_points([LaserPoint(i, x, y, *rgb) for i in range(num_lasers)])
        d = (d + 8) % 360

def letters(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
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

def images(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
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

def spirograph(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    r1 = 105
    r2 = 75
    scale = 4
    x = 0.5
    xd = 1
    r2d = 1
    t = 0
    while True:
        q1 = t
        s1 = np.sin(q1)
        c1 = np.cos(q1)
        q2 = q1 * r1 / r2
        s2 = np.sin(q2)
        c2 = np.cos(q2)
        xx = int((r1 * s1 + x * r2 * (-s1 + c2 * s1 - c1 * s2)) * scale) + 2048
        yy = int((-r1 * c1 + x * r2 * (c1 - c1 * c2 - s1 * s2)) * scale) + 2048
        yield verify_points([LaserPoint(i, xx, yy, 255, 0, 0) for i in range(num_lasers)])

        x += 0.00000002 * xd
        if x > 0.9 or x < 0.3:
            xd *= -1
        
        r2 += 0.0000002 * r2d
        if r2 > 78 or r2 < 40:
            r2d *= -1
        
        t += 0.2

def bouncing_ball(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    bounds = sierpinski.get_laser_coordinate_bounds()
    x_transitions = sorted([b[0] for b in bounds])
    min_x = min(b[0] for b in bounds)
    max_x = max(b[0] for b in bounds)
    min_y = min(b[1] for b in bounds)
    max_y = max(b[1] for b in bounds)
    ball_radius = 20
    ball_laser = 0
    ball_x = (max_x - min_x) / 2 + min_x
    ball_y = (max_y - min_y) / 2 + min_y
    dx = 2
    dy = 2

    while True:
        ball_x += dx
        ball_y += dy

        if x_transitions[0] <= ball_x <= x_transitions[1]:
            y_limit = np.interp(ball_x, [x_transitions[0], x_transitions[1]], [min_y, max_y])
            if ball_y > y_limit:
                ball_laser = (ball_laser + num_lasers - 1) % num_lasers
                ball_x = np.interp(ball_y, [min_y, max_y], [x_transitions[3], x_transitions[2]])
        elif x_transitions[2] <= ball_x <= x_transitions[3]:
            y_limit = np.interp(ball_x, [x_transitions[2], x_transitions[3]], [max_y, min_y])
            if ball_y > y_limit:
                ball_laser = (ball_laser + 1) % num_lasers
                ball_x = np.interp(ball_y, [min_y, max_y], [x_transitions[0], x_transitions[1]])

        if ball_y + ball_radius > max_y or ball_y - ball_radius < min_y:
            dy *= -1

        for d in range(0, 360, 30):
            x = int(ball_radius * np.sin(d * np.pi / 180) + ball_x)
            y = int(ball_radius * np.cos(d * np.pi / 180) + ball_y)
            data = [LaserPoint(i) for i in range(num_lasers)]
            data[ball_laser] = LaserPoint(ball_laser, x, y, 255, 0, 0)
            yield verify_points(data)
    