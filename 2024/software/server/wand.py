"""Defines the Wand Class"""

import colorsys
import pygame
import pyquaternion
import sierpinski
import laser_point
import numpy as np
import pyautogui

class Wand:
    def __init__(self, joystick: pygame.joystick.Joystick) -> None:
        self.BASE_QUATERNION = pyquaternion.Quaternion(1, 0, 0, -1)
        self.BASE_VECTOR_START = np.array([-1, 0, 0])
        self.BASE_VECTOR_END = np.array([1, 0, 0])
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.4

        self.joystick = joystick
        self.position = None
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None

    def quit(self) -> None:
        self.joystick.quit()
        
    def get_rotation_angle(self) -> int:
        v0 = self.position.rotate([0, 1, 0])
        v1 = self.position.rotate([1, 0, 0])
        v2 = np.array([-1.0 * v1[0] * v1[2], -1.0 * v1[1] * v1[2], v1[0]**2 + v1[1]**2]) / np.sqrt(v1[0]**2 + v1[1]**2)
        v3 = np.cross(v1, v2)
        phi1 = int(np.degrees(np.arccos(np.dot(v0, v2))))
        phi2 = int(np.degrees(np.arccos(np.dot(v0, v3))))
        return phi1 if phi2 < 90 else 360 - phi1

    def get_wand_color(self) -> list[int]:
        r, g, b = colorsys.hsv_to_rgb(self.get_rotation_angle() / 360, 1, 1)
        return [int(r * 255), int(g * 255), int(b * 255)]

    def get_laser_point(self) -> laser_point.LaserPoint:
        start = self.position.rotate(self.BASE_VECTOR_START)
        end = self.position.rotate(self.BASE_VECTOR_END)
        start[2] += sierpinski.HUMAN_HEIGHT
        end[2] += sierpinski.HUMAN_HEIGHT
        wand_projection = sierpinski.get_wand_projection(start, end)
        if wand_projection:
            laser_index, wand_point = wand_projection
            laser_x, laser_y = sierpinski.sierpinski_to_laser_coords(laser_index, *wand_point)
            return laser_point.LaserPoint(laser_index, int(laser_x), int(laser_y), *self.get_wand_color())
        else:
            return None

    def update_position(self) -> None:
        q = pyquaternion.Quaternion(w=self.joystick.get_axis(5), 
                                    x=self.joystick.get_axis(0), 
                                    y=self.joystick.get_axis(1), 
                                    z=self.joystick.get_axis(2))
        if not self.cal_offset:
            init_vector = self.BASE_QUATERNION.rotate(q).rotate([1, 0, 0])
            self.cal_offset = sierpinski.find_quat(init_vector, sierpinski.target_vector)
        self.position = self.cal_offset * self.BASE_QUATERNION.rotate(q)
        tip_pos = self.position.rotate(self.BASE_VECTOR_END)[2]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append(tip_pos)
        new_speed = self.pos_queue[-1] - self.pos_queue[0]
        if self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD and self.callback:
            self.callback()
        self.prev_speed = new_speed
        
class WandSimulator:
    def __init__(self) -> None:
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 300

        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.screen_width, self.screen_height = pyautogui.size()
        self.position = [0, 0]
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0

    def quit(self) -> None:
        pass
        
    def get_rotation_angle(self) -> int:
        return 0

    def get_wand_color(self) -> list[int]:
        r, g, b = colorsys.hsv_to_rgb(self.get_rotation_angle() / 360, 1, 1)
        return [int(r * 255), int(g * 255), int(b * 255)]

    def get_laser_point(self) -> laser_point.LaserPoint:
        return laser_point.LaserPoint(0, int(self.position[0]), int(self.position[1]), *self.get_wand_color())

    def update_position(self) -> None:
        mouse = pyautogui.position()
        x = np.interp(mouse.x, [0, self.screen_width], [self.min_x, self.max_x])
        y = np.interp(mouse.y, [0, self.screen_height], [self.max_y, self.min_y])
        self.position = [x, y]

        tip_pos = self.position[1]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append(tip_pos)
        new_speed = -(self.pos_queue[-1] - self.pos_queue[0])
        if self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD and self.callback:
            self.callback()
        self.prev_speed = new_speed
