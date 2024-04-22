"""This module defines laser graphics generators"""

import colorsys
import random
import time
import numpy as np
from laser_point import *
from laser_objects import *
from typing import Generator
import sierpinski

current_effect = None
current_song = None
current_wands = None

def verify_points(points: list[LaserPoint]) -> list[LaserPoint]:
    """Constrains point values to valid ranges"""
    for p in points:
        p.x = int(min(max(p.x, 0), 4095))
        p.y = int(min(max(p.y, 0), 4095))
        p.r = int(min(max(p.r, 0), 255))
        p.g = int(min(max(p.g, 0), 255))
        p.b = int(min(max(p.b, 0), 255))
    return points

def drums(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates an audio-reactive rgb circle"""
    min_x, max_x, min_y, max_y = sierpinski.get_laser_min_max_interior()
    x_offset = (min_x + max_x) // 2
    y_offset = (min_y + max_y) // 2
    sample_blocksize = 256
    sample_interval = 8

    rotation = 0
    d = 0
    amplitude = 100
    while True:
        if d == 0:
            rotation += 0.2
            if current_effect:
                amplitude = 100 + current_effect.get_amplitude(sample_blocksize * sample_interval, sample_interval) * 300
            else:
                amplitude = 100
 
        x = (50 + amplitude) * np.sin(d * np.pi / 180) + x_offset
        y = (50 + amplitude) * np.cos(d * np.pi / 180) + y_offset
        r, g, b = colorsys.hsv_to_rgb((int(rotation + d) % 360) / 360, 1, 1)
        yield verify_points([LaserPoint(i, x, y, r * 255, g * 255, b * 255) for i in range(num_lasers)])
        d = (d + 8) % 360

def equations(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates equation graphics on three lasers"""
    min_x, max_x, min_y, max_y = sierpinski.get_laser_min_max_interior()
    colors = [[0, 0, 255], [0, 255, 0], [255, 0, 0], [0, 255, 255], [255, 255, 0], [255, 0, 255], [255, 255, 255]]

    equation_list = [ EQN_01, EQN_02, EQN_03, EQN_04, EQN_05, EQN_06, EQN_07, EQN_08, 
                      EQN_09, EQN_10, EQN_11, EQN_12, EQN_13, EQN_14, EQN_15, EQN_16, 
                      EQN_17, EQN_18, EQN_19, EQN_20, EQN_21, EQN_22, EQN_23, EQN_24, 
                      EQN_25, EQN_26, EQN_27, EQN_28, EQN_29, EQN_30, EQN_31, EQN_32, 
                      EQN_33, EQN_34, EQN_35, EQN_36 ]
    
    scaled_equations = [interpolate_objects(convert_to_xy(eq, x_scale=0.5, y_scale=0.5)) for eq in equation_list]
    equation_sizes = [get_size(eq) for eq in scaled_equations]
    
    point_idxs = [0 for _ in range(num_lasers)]
    offsets = [[(min_x + max_x) // 2, (min_y + max_y) // 2] for _ in range(num_lasers)]
    dirs = [[2, 2] for _ in range(num_lasers)]
    eqn_idxs = [i % len(equation_list) for i in range(num_lasers)]
    color_idxs = [i % len(colors) for i in range(num_lasers)]

    next_update = 0
    while True:
        if time.time() > next_update:
            for i in range(num_lasers):
                eqn_idxs[i] = (eqn_idxs[i] + num_lasers) % len(equation_list)
                color_idxs[i] = (color_idxs[i] + num_lasers) % len(colors)
                point_idxs[i] = 0
            next_update = time.time() + 30

        output = []
        for i in range(num_lasers):
            x, y, on = scaled_equations[eqn_idxs[i]][point_idxs[i]]
            x += offsets[i][0]
            y += offsets[i][1]
            output.append(LaserPoint(i, x, y, *(colors[color_idxs[i]] if on else [0, 0, 0])))

            point_idxs[i] = (point_idxs[i] + 1) % len(scaled_equations[eqn_idxs[i]])
            if point_idxs[i] == 0:
                offsets[i][0] += dirs[i][0]
                offsets[i][1] += dirs[i][1]
                if offsets[i][0] + equation_sizes[eqn_idxs[i]][0] / 2 > max_x and dirs[i][0] > 0:
                    dirs[i][0] *= -1
                elif offsets[i][0] - equation_sizes[eqn_idxs[i]][0] / 2 < min_x and dirs[i][0] < 0:
                    dirs[i][0] *= -1
                if offsets[i][1] + equation_sizes[eqn_idxs[i]][1] / 2 > max_y and dirs[i][1] > 0:
                    dirs[i][1] *= -1
                elif offsets[i][1] - equation_sizes[eqn_idxs[i]][1] / 2 < min_y and dirs[i][1] < 0:
                    dirs[i][1] *= -1

        yield verify_points(output)

class Spirograph:
    def __init__(self, r1: float, r2: float, a: float, t_d: float) -> None:
        self.params = { 'r1': r1, 'r2': r2, 'a': a }
        self.deltas = {}
        self.t = 0
        self.t_d = t_d
        self.x = 0
        self.y = 0

    def add_delta(self, param: str, delta: float, lower_limit: float, upper_limit: float) -> None:
        self.deltas[param] = [delta, lower_limit, upper_limit]

    def remove_delta(self, param: str) -> None:
        del self.deltas[param]

    def update(self, x_scale: float=1, y_scale: float=1, 
               x_offset: float=0, y_offset: float=0) -> tuple[float, float]:
        self.t += self.t_d
        for delta in self.deltas:
            self.params[delta] += self.deltas[delta][0]
            if self.params[delta] < self.deltas[delta][1] or self.params[delta] > self.deltas[delta][2]:
                self.deltas[delta][0] *= -1

        q1 = self.t
        s1 = np.sin(q1)
        c1 = np.cos(q1)
        q2 = q1 * self.params['r1'] / self.params['r2']
        s2 = np.sin(q2)
        c2 = np.cos(q2)
        x = self.params['r1'] * s1 + self.params['a'] * self.params['r2'] * (-s1 + c2 * s1 - c1 * s2)
        y = -self.params['r1'] * c1 + self.params['a'] * self.params['r2'] * (c1 - c1 * c2 - s1 * s2)
        self.x = x * x_scale + x_offset
        self.y = y * y_scale + y_offset
        return (self.x, self.y)

def spirograph(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates random spirographs"""
    min_x, max_x, min_y, max_y = sierpinski.get_laser_min_max_interior()

    spiros = [Spirograph(r1=random.uniform(100, 110),
                         r2=random.uniform(40, 80), 
                         a=random.uniform(0.3, 0.9),
                         t_d=random.uniform(0.15, 0.25))
                         for _ in range(num_lasers)] 
    
    for i in range(num_lasers):
        spiros[i].add_delta('r2', 0.00000002, 40, 80)
        spiros[i].add_delta('a', 0.000000002, 0.3, 0.9)

    xs, ys = 1.5, 1.5
    offsets = [[(min_x + max_x) // 2, (min_y + max_y) // 2] for _ in range(num_lasers)]
    dirs = [[0.01, 0.01] for _ in range(num_lasers)]
    for dir in dirs:
        dir[0] *= random.choice([1, -1])
        dir[1] *= random.choice([1, -1])
    colors = [random.uniform(0, 0.9) for _ in range(num_lasers)]
    iteration = 0
    point_mode = True
    next_update = 0

    while True:
        if time.time() > next_update:
            point_mode = not point_mode
            next_update = time.time() + 30

        iteration += 1
        output = []

        for i in range(num_lasers):  
            r, g, b = colorsys.hsv_to_rgb(colors[i], 1, 1)
            if not point_mode:
                output.append(LaserPoint(i, *spiros[i].update(xs, ys, offsets[i][0], offsets[i][1]), r * 255, g * 255, b * 255))
            elif iteration % 3 == 0:
                output.append(LaserPoint(i, spiros[i].x, spiros[i].y, 0, 0, 0))  
            elif iteration % 3 == 1:
                output.append(LaserPoint(i, spiros[i].x, spiros[i].y, r * 255, g * 255, b * 255))
            else:
                output.append(LaserPoint(i, *spiros[i].update(xs, ys, offsets[i][0], offsets[i][1]), 0, 0, 0))
            
            colors[i] += 0.00001
            if colors[i] > 1:
                colors[i] = 0

            offsets[i][0] += dirs[i][0]
            offsets[i][1] += dirs[i][1]
            if spiros[i].x > max_x and dirs[i][0] > 0:
                dirs[i][0] *= -1
            elif spiros[i].x < min_x and dirs[i][0] < 0:
                dirs[i][0] *= -1
            if spiros[i].y > max_y and dirs[i][1] > 0:
                dirs[i][1] *= -1
            elif spiros[i].y < min_y and dirs[i][1] < 0:
                dirs[i][1] *= -1

        yield verify_points(output)
        

def pong(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    bounds = sierpinski.get_laser_coordinate_bounds()
    _xs = sorted([b[0] for b in bounds])
    min_x, max_x = min(b[0] for b in bounds), max(b[0] for b in bounds)
    min_y, max_y = min(b[1] for b in bounds), max(b[1] for b in bounds)
    center_x = (max_x + min_x) // 2
    center_y = (max_y + min_y) // 2
    ball_radius = 20
    ball_laser = 1
    ball_x = center_x
    ball_y = center_y
    dx = 2
    dy = 2

    ai_paddle_speed = 2
    paddle_gap = 60
    paddle_half_height = 100
    left_paddle = center_y
    right_paddle = center_y
    left_paddle_speed = 0
    right_paddle_speed = 0
    score_timeout = False
    game_reset_time = 0

    def calculate_new_angle():
        return (dx * -1, dy)
    
    def new_paddle_pos(old_pos, curr_speed, delta):
        return (old_pos + delta, 0.25 * curr_speed + 0.75 * delta)

    while True:
        if score_timeout and time.time() > game_reset_time:
            score_timeout = False
            ball_x = center_x
            ball_y = center_y
            ball_laser = 1
            dx = 2
            dy = 2

        if not score_timeout:
            ball_x += dx
            ball_y += dy

            if _xs[0] <= ball_x <= _xs[1]:
                y_limit = np.interp(ball_x, [_xs[0], _xs[1]], [min_y, max_y])
                if ball_y > y_limit:
                    ball_laser = (ball_laser + num_lasers - 1) % num_lasers
                    ball_x = np.interp(ball_y, [min_y, max_y], [_xs[3], _xs[2]])
            elif _xs[2] <= ball_x <= _xs[3]:
                y_limit = np.interp(ball_x, [_xs[2], _xs[3]], [max_y, min_y])
                if ball_y > y_limit:
                    ball_laser = (ball_laser + 1) % num_lasers
                    ball_x = np.interp(ball_y, [min_y, max_y], [_xs[0], _xs[1]])

            if (ball_y + ball_radius > max_y and dy > 0) or (ball_y - ball_radius < min_y and dy < 0):
                dy *= -1

            if ball_laser == 0 and center_x - paddle_gap < ball_x < center_x and dx > 0:
                if abs(ball_y - left_paddle) < paddle_half_height:
                    dx, dy = calculate_new_angle()
                else:
                    score_timeout = True
                    game_reset_time = time.time() + 3
            elif ball_laser == 0 and center_x < ball_x < center_x + paddle_gap and dx < 0:
                if abs(ball_y - right_paddle) < paddle_half_height:
                    dx, dy = calculate_new_angle()
                else:
                    score_timeout = True
                    game_reset_time = time.time() + 3

        for d in range(0, 360, 30):
            x = ball_radius * np.sin(d * np.pi / 180) + ball_x
            y = ball_radius * np.cos(d * np.pi / 180) + ball_y
            data = [LaserPoint(i) for i in range(num_lasers)]
            data[ball_laser] = LaserPoint(ball_laser, x, y, 0, 0, 255 if d != 0 else 0)
            yield verify_points(data)

        paddle_points = [LaserPoint(0, center_x - paddle_gap, left_paddle - paddle_half_height, 0, 0, 0),
                         LaserPoint(0, center_x - paddle_gap, left_paddle + paddle_half_height, 0, 255, 0),
                         LaserPoint(0, center_x + paddle_gap, right_paddle - paddle_half_height, 0, 0, 0),
                         LaserPoint(0, center_x + paddle_gap, right_paddle + paddle_half_height, 0, 255, 0)]
        for p in paddle_points:
            yield verify_points([LaserPoint(i) if i > 0 else p for i in range(num_lasers)])

        if not score_timeout:
            if len(current_wands) > 0:
                if lp := list(current_wands.values())[0].get_laser_point():
                    left_paddle, left_paddle_speed = new_paddle_pos(left_paddle, left_paddle_speed, 
                            max(min(lp.y, max_y - paddle_half_height), min_y + paddle_half_height) - left_paddle)
            else:
                if left_paddle < ball_y and left_paddle + paddle_half_height < max_y:
                    left_paddle, left_paddle_speed = new_paddle_pos(left_paddle, left_paddle_speed, ai_paddle_speed)
                elif left_paddle > ball_y and left_paddle - paddle_half_height > min_y:
                    left_paddle, left_paddle_speed = new_paddle_pos(left_paddle, left_paddle_speed, -ai_paddle_speed)
            
            if len(current_wands) > 1:
                if lp := list(current_wands.values())[1].get_laser_point():
                   right_paddle, right_paddle_speed = new_paddle_pos(right_paddle, right_paddle_speed, 
                            max(min(lp.y, max_y - paddle_half_height), min_y + paddle_half_height) - right_paddle)
            else:
                if right_paddle < ball_y and right_paddle + paddle_half_height < max_y:
                    right_paddle, right_paddle_speed = new_paddle_pos(right_paddle, right_paddle_speed, ai_paddle_speed)
                elif right_paddle > ball_y and right_paddle - paddle_half_height > min_y:
                    right_paddle, right_paddle_speed = new_paddle_pos(right_paddle, right_paddle_speed, -ai_paddle_speed)
        

def audio_visualization(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    """Generates an audio visualization"""
    min_x, max_x, min_y, max_y = sierpinski.get_laser_min_max_interior()
    base_y = (max_y + min_y) / 2
    sample_blocksize = 256
    sample_interval = 8
    xs = np.linspace(min_x, max_x, num=sample_blocksize)
    ys = [base_y for _ in range(sample_blocksize)]
    index = 0
    colors = [colorsys.hsv_to_rgb(abs(i - base_y) / 600, 1, 1) for i in range(4095)]
    for i in range(len(colors)):
        colors[i] = (colors[i][0] * 255, colors[i][1] * 255, colors[i][2] * 255)

    while True:
        if index == 0:
            if current_song and (audio_data := current_song.get_envelope(sample_blocksize * sample_interval, sample_interval, 0.05)):
                audio_data = current_song.center_on_peak(audio_data, sample_blocksize // 10)
                ys = [base_y + v * 300 for v in audio_data]
                while len(ys) < sample_blocksize:
                    ys.append(base_y)
            else:
                ys = [base_y for _ in range(sample_blocksize)]
        
        if index == 0:
            yield verify_points([LaserPoint(i, xs[-1], ys[-1], 0, 0, 0) for i in range(num_lasers)])
            yield verify_points([LaserPoint(i, xs[0], ys[0], 0, 0, 0) for i in range(num_lasers)])
        else:
            rgb = colors[int(ys[index])] if ys[index] < len(colors) else [0, 0, 0]
            yield verify_points([LaserPoint(i, xs[index], ys[index], *rgb) for i in range(num_lasers)])
        index = (index + 1) % sample_blocksize

def wand_drawing(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    PATH_TIME = 3
    DELTA_TIME = 0.1
    paths = {}
    current_path = 0
    path_index = 0
    next_update = 0
    
    while True:
        if time.time() > next_update:
            if current_wands is not None:
                for path in list(paths):
                    if path not in current_wands:
                        del paths[path]
                for wand in current_wands:
                    if wand not in paths:
                        paths[wand] = []
                    if lp := current_wands[wand].get_laser_point():
                        paths[wand].append(lp)
            for path in paths.values():
                while len(path) > PATH_TIME / DELTA_TIME:
                    path.pop(0)
            next_update = time.time() + DELTA_TIME

        data = [LaserPoint(i) for i in range(num_lasers)]
        if len(paths) == 0:
            yield data
        else:
            current_path = current_path % len(paths)
            p = list(paths.values())[current_path]
            path_index = path_index % len(p)

            if path_index == 0:
                data[p[path_index].id] = LaserPoint(p[path_index].id, p[path_index].x, p[path_index].y, 0, 0, 0)
            else:
                data[p[path_index].id] = p[path_index]
            
            yield verify_points(data)

            if path_index == len(p) - 1:
                data[p[path_index].id] = LaserPoint(p[path_index].id, p[path_index].x, p[path_index].y, 0, 0, 0)
                yield verify_points(data)

            if (path_index := (path_index + 1) % len(p)) == 0:
                current_path = (current_path + 1) % len(paths)

def calibration(num_lasers: int) -> Generator[list[LaserPoint], None, None]:
    bounds = sierpinski.get_laser_coordinate_bounds()
    points = [[int(b[0]), int(b[1]), 1] for b in bounds]
    points.append(points[0])
    points = interpolate_objects(points)
    index = 0
    
    while True:
        x, y, on = points[index]
        yield [LaserPoint(i, x, y, 0, 255 if on else 0, 0) for i in range(num_lasers)]
        index = (index + 1) % len(points)
