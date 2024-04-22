"""Defines various Wand implementations"""

import enum
import colorsys
import threading
import pygame
import pyquaternion
import sierpinski
import laser_point
import numpy as np
import pyautogui
import asyncio
import bleak

class Wand:
    def __init__(self, joystick: pygame.joystick.Joystick, pump: bool=False) -> None:
        self.BASE_QUATERNION = pyquaternion.Quaternion(1, 0, 0, -1)
        self.BASE_VECTOR_START = np.array([-1, 0, 0])
        self.BASE_VECTOR_END = np.array([1, 0, 0])
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.3

        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.joystick = joystick
        self.position = None
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None
        self.pump = pump

    def __repr__(self):
        return f'Wand(ID: {self.joystick.get_instance_id()})'

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

    def get_synth_point(self) -> list[float]:
        if lp := self.get_laser_point():
            x = np.interp(lp.x, [self.min_x, self.max_x], [0, 1])
            y = np.interp(lp.y, [self.min_y, self.max_y], [0, 1])
            r = np.interp(self.get_rotation_angle(), [0, 360], [0, 1])
            return (x, y, r)
        else:
            return None

    def get_laser_point(self) -> laser_point.LaserPoint:
        if self.position is None:
            return None
        start = self.position.rotate(self.BASE_VECTOR_START)
        end = self.position.rotate(self.BASE_VECTOR_END)
        start[2] += sierpinski.HUMAN_HEIGHT
        end[2] += sierpinski.HUMAN_HEIGHT
        if wand_projection := sierpinski.get_wand_projection(start, end):
            laser_index, wand_point = wand_projection
            laser_x, laser_y = sierpinski.sierpinski_to_laser_coords(laser_index, *wand_point)
            return laser_point.LaserPoint(laser_index, int(laser_x), int(laser_y), *self.get_wand_color())
        else:
            return None

    def update_position(self) -> pyquaternion.quaternion:
        if self.pump:
            pygame.event.pump()
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
        return self.position
        
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

    def __repr__(self):
        return 'WandSimulator()'

    def quit(self) -> None:
        pass
        
    def get_rotation_angle(self) -> int:
        return 0

    def get_wand_color(self) -> list[int]:
        r, g, b = colorsys.hsv_to_rgb(self.get_rotation_angle() / 360, 1, 1)
        return [int(r * 255), int(g * 255), int(b * 255)]

    def get_synth_point(self) -> list[float]:
        lp = self.get_laser_point()
        x = np.interp(lp.x, [self.min_x, self.max_x], [0, 1])
        y = np.interp(lp.y, [self.min_y, self.max_y], [0, 1])
        r = np.interp(self.get_rotation_angle(), [0, 360], [0, 1])
        return (x, y, r)

    def get_laser_point(self) -> laser_point.LaserPoint:
        return laser_point.LaserPoint(0, int(self.position[0]), int(self.position[1]), *self.get_wand_color())

    def update_position(self) -> tuple[float, float]:
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
        return self.position


class KANO_INFO(enum.Enum):
    SERVICE = '64a70010-f691-4b93-a6f4-0968f5b648f8'
    ORGANIZATION_CHAR = '64a7000b-f691-4b93-a6f4-0968f5b648f8'
    SOFTWARE_CHAR = '64a70013-f691-4b93-a6f4-0968f5b648f8'
    HARDWARE_CHAR = '64a70001-f691-4b93-a6f4-0968f5b648f8'

class KANO_IO(enum.Enum):
    SERVICE = '64a70012-f691-4b93-a6f4-0968f5b648f8'
    BATTERY_CHAR = '64a70007-f691-4b93-a6f4-0968f5b648f8'
    USER_BUTTON_CHAR = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    VIBRATOR_CHAR = '64a70008-f691-4b93-a6f4-0968f5b648f8'
    LED_CHAR = '64a70009-f691-4b93-a6f4-0968f5b648f8'
    KEEP_ALIVE_CHAR = '64a7000f-f691-4b93-a6f4-0968f5b648f8'

class KANO_SENSOR(enum.Enum):
    SERVICE = '64a70011-f691-4b93-a6f4-0968f5b648f8'
    TEMP_CHAR = '64a70014-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_CHAR = '64a70002-f691-4b93-a6f4-0968f5b648f8'
    # RAW_CHAR = '64a7000a-f691-4b93-a6f4-0968f5b648f8'
    # MOTION_CHAR = '64a7000c-f691-4b93-a6f4-0968f5b648f8'
    MAGN_CALIBRATE_CHAR = '64a70021-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_RESET_CHAR = '64a70004-f691-4b93-a6f4-0968f5b648f8'

class KANO_PATTERN(enum.Enum):
    REGULAR = 1
    SHORT = 2
    BURST = 3
    LONG = 4
    SHORT_LONG = 5
    SHORT_SHORT = 6
    BIG_PAUSE = 7

class KanoWand(object):
    """A wand class to interact with the Kano wand"""

    def __init__(self, device_addr, name, bleak_loop):
        self.BASE_QUATERNION = pyquaternion.Quaternion(1, 0, 0, -1)
        self.BASE_VECTOR_START = np.array([-1, 0, 0])
        self.BASE_VECTOR_END = np.array([1, 0, 0])
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.4

        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.position = None
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None

        self._dev = bleak.BleakClient(device_addr)
        self.name = name
        self._bleak_loop = bleak_loop
        self.position_raw = None

        print(f'Connecting to {self.name}...')
        connected = self._await_bleak(self._dev.connect())
        if not connected:
            raise Exception(f'Could not connect to {self.name}')
        
        self._await_bleak(self._dev.write_gatt_char(KANO_IO.KEEP_ALIVE_CHAR.value, bytearray([1]), response=True))
        self._org = self._await_bleak(self._dev.read_gatt_char(KANO_INFO.ORGANIZATION_CHAR.value)).decode('utf-8')
        self._sw_ver = self._await_bleak(self._dev.read_gatt_char(KANO_INFO.SOFTWARE_CHAR.value)).decode('utf-8')
        self._hw_ver = self._await_bleak(self._dev.read_gatt_char(KANO_INFO.HARDWARE_CHAR.value)).decode('utf-8')
        #self._await_bleak(self._dev.start_notify(KANO_SENSOR.QUATERNIONS_CHAR.value, self._handle_notification))
        #self._await_bleak(self._dev.start_notify(KANO_IO.USER_BUTTON_CHAR.value, self._handle_notification))
        self.connected = True
        print(f'Connected to {self.name}')

    def __repr__(self):
        return f'KanoWand(Name: {self.name}, Address: {self._dev.address}, Org: {self._org}, SW Ver: {self._sw_ver}, HW Ver: {self._hw_ver})'
    
    def _await_bleak(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._bleak_loop).result()

    def _handle_notification(self, sender, data):
        if sender == KANO_SENSOR.QUATERNIONS_CHAR.value:
            self.get_position_raw(data)
        elif sender == KANO_IO.USER_BUTTON_CHAR.value:
            self.get_button(data)

    def quit(self) -> None:
        if self.connected:
            self._await_bleak(self._dev.disconnect())
            self.connected = False
            print(f'Disconnected from {self.name}')
        
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

    def get_synth_point(self) -> list[float]:
        if lp := self.get_laser_point():
            x = np.interp(lp.x, [self.min_x, self.max_x], [0, 1])
            y = np.interp(lp.y, [self.min_y, self.max_y], [0, 1])
            r = np.interp(self.get_rotation_angle(), [0, 360], [0, 1])
            return (x, y, r)
        else:
            return None

    def get_laser_point(self) -> laser_point.LaserPoint:
        start = self.position.rotate(self.BASE_VECTOR_START)
        end = self.position.rotate(self.BASE_VECTOR_END)
        start[2] += sierpinski.HUMAN_HEIGHT
        end[2] += sierpinski.HUMAN_HEIGHT
        if wand_projection := sierpinski.get_wand_projection(start, end):
            laser_index, wand_point = wand_projection
            laser_x, laser_y = sierpinski.sierpinski_to_laser_coords(laser_index, *wand_point)
            return laser_point.LaserPoint(laser_index, int(laser_x), int(laser_y), *self.get_wand_color())
        else:
            return None

    def update_position(self) -> pyquaternion.Quaternion:
        x, y, z, w = self.get_position_raw() # or self.position_raw if using notify
        q = pyquaternion.Quaternion(w=w, x=x, y=y, z=z)
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
        return self.position

    def reset_position(self):
        self._await_bleak(self._dev.write_gatt_char(KANO_SENSOR.QUATERNIONS_RESET_CHAR.value, bytearray([1]), response=True))

    def get_position_raw(self, data=None):
        if data is None:
            data = self._await_bleak(self._dev.read_gatt_char(KANO_SENSOR.QUATERNIONS_CHAR.value))
        y = np.int16(np.uint16(int.from_bytes(data[0:2], byteorder='little')))
        x = -1 * np.int16(np.uint16(int.from_bytes(data[2:4], byteorder='little')))
        w = -1 * np.int16(np.uint16(int.from_bytes(data[4:6], byteorder='little')))
        z = np.int16(np.uint16(int.from_bytes(data[6:8], byteorder='little')))
        self.position_raw = (x, y, z, w)
        return self.position_raw

    def get_button(self, data=None):
        if data is None:
            data = self._await_bleak(self._dev.read_gatt_char(KANO_IO.USER_BUTTON_CHAR.value))
        self.button = data[0] == 1
        return self.button

    def vibrate(self, pattern=KANO_PATTERN.REGULAR):
        message = [pattern.value if isinstance(pattern, KANO_PATTERN) else pattern]
        self._await_bleak(self._dev.write_gatt_char(KANO_IO.VIBRATOR_CHAR.value, bytearray(message), response=True))

    def set_led(self, r, g, b, on=True):
        rgb = (((r & 248) << 8) + ((g & 252) << 3) + ((b & 248) >> 3))
        message = [1 if on else 0, rgb >> 8, rgb & 0xff]
        self._await_bleak(self._dev.write_gatt_char(KANO_IO.LED_CHAR.value, bytearray(message), response=True))

class KanoHandler(object):
    """A scanner class to connect to wands"""

    def __init__(self):
        self._bleak_loop = None
        self._bleak_thread = threading.Thread(target=self._run_bleak_loop, daemon=True)
        self._bleak_thread_ready = threading.Event()
        self._bleak_thread.start()
        self._bleak_thread_ready.wait()

    def _run_bleak_loop(self):
        self._bleak_loop = asyncio.new_event_loop()
        self._bleak_thread_ready.set()
        self._bleak_loop.run_forever()

    def scan(self, prefix="Kano-Wand", mac=None):
        devices = asyncio.run_coroutine_threadsafe(bleak.BleakScanner.discover(timeout=2.0), self._bleak_loop).result()
        # print(devices)
        if prefix:
            devices = [d for d in devices if d.name is not None and d.name.startswith(prefix)]
        if mac:
            devices = [d for d in devices if d.address == mac]
        # print(devices)
        wands = [Wand(d.address, d.name, self._bleak_loop) for d in devices]
        # print(self.wands)
        return wands
    

if __name__ == '__main__':
    wands = []

    kano_handler = KanoHandler()
    wands.extend(kano_handler.scan())
    
    pygame.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        if joystick.get_numaxes() >= 8:
            wands.append(Wand(joystick, pump=True))
        else:
            joystick.quit()
 
    if not wands:
        wands.append(WandSimulator())

    print('Found wands:', [wand for wand in wands])
