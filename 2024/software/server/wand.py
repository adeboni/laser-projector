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
import time

KANO_WAND_CONNECT = pygame.USEREVENT + 1
KANO_WAND_DISCONNECT = pygame.USEREVENT + 2

class WandBase:
    def __init__(self) -> None:
        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.position = None
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None
        self.position = pyquaternion.Quaternion()
        self.reset_cal = False
        self.last_angle = 0

    def get_rotation_angle(self) -> int:
        if self.position is None:
            return self.last_angle
        v0 = self.position.rotate([0, 1, 0])
        v1 = self.position.rotate([1, 0, 0])
        v2 = np.array([-1.0 * v1[0] * v1[2], -1.0 * v1[1] * v1[2], v1[0]**2 + v1[1]**2]) / np.sqrt(v1[0]**2 + v1[1]**2)
        v3 = np.cross(v1, v2)
        d1, d2 = np.dot(v0, v2), np.dot(v0, v3)
        if np.isnan(d1) or np.isnan(d2):
            return self.last_angle
        d1, d2 = np.arccos(np.clip(d1, -1, 1)), np.arccos(np.clip(d2, -1, 1))
        if np.isnan(d1) or np.isnan(d2):
            return self.last_angle
        phi1 = int(np.degrees(d1))
        phi2 = int(np.degrees(d2))
        self.last_angle = phi1 if phi2 < 90 else 360 - phi1
        return self.last_angle

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
        if wand_projection := sierpinski.get_wand_projection(self.position):
            laser_index, wand_point = wand_projection
            laser_x, laser_y = sierpinski.sierpinski_to_laser_coords(laser_index, *wand_point)
            return laser_point.LaserPoint(laser_index, int(laser_x), int(laser_y), *self.get_wand_color())
        else:
            return None

class Wand(WandBase):
    def __init__(self, joystick: pygame.joystick.Joystick, pump: bool=False) -> None:
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=0, y=0, z=1)
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.3
        self.joystick = joystick
        self.pump = pump
        self.connected = True

    def __repr__(self):
        return f'Wand(ID: {self.joystick.get_instance_id()})'

    def quit(self) -> None:
        self.connected = False
        self.joystick.quit()
        
    def update_position(self) -> None:
        if not self.connected:
            return
        if self.pump:
            pygame.event.pump()
        position_raw = pyquaternion.Quaternion(w=self.joystick.get_axis(5), 
                                                    x=self.joystick.get_axis(0), 
                                                    y=self.joystick.get_axis(1), 
                                                    z=self.joystick.get_axis(2))
        # if self.joystick.get_button(1):
        #     self.reset_cal = True
        if not self.cal_offset or self.reset_cal:
            self.cal_offset = self.BASE_2.rotate(self.BASE_1.rotate(position_raw)).inverse
            self.reset_cal = False
        self.position = self.cal_offset * self.BASE_2.rotate(self.BASE_1.rotate(position_raw))
        
        tip_pos = self.position.rotate([1, 0, 0])[2]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append(tip_pos)
        new_speed = self.pos_queue[0] - self.pos_queue[-1]
        if self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD and self.callback:
            self.callback()
        self.prev_speed = new_speed
        
class WandSimulator(WandBase):
    def __init__(self) -> None:
        super().__init__()
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.3
        self.screen_width, self.screen_height = pyautogui.size()
        self.connected = True

    def __repr__(self):
        return 'WandSimulatorQuat()'

    def quit(self) -> None:
        self.connected = False

    def update_position(self) -> None:
        if not self.connected:
            return
        mouse = pyautogui.position()
        x = np.interp(mouse.x, [0, self.screen_width], [1, -1])
        y = np.interp(mouse.y, [0, self.screen_height], [-1, 1])
        self.position = pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                      * pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                      * pyquaternion.Quaternion(w=1, x=0, y=0, z=x) \
                      * pyquaternion.Quaternion(w=1, x=0, y=0, z=x)

        tip_pos = self.position.rotate([1, 0, 0])[2]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append(tip_pos)
        new_speed = self.pos_queue[0] - self.pos_queue[-1]
        if self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD and self.callback:
            self.callback()
        self.prev_speed = new_speed

class KANO_IO(enum.Enum):
    USER_BUTTON_CHAR = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    VIBRATOR_CHAR = '64a70008-f691-4b93-a6f4-0968f5b648f8'
    LED_CHAR = '64a70009-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_CHAR = '64a70002-f691-4b93-a6f4-0968f5b648f8'

class KANO_PATTERN(enum.Enum):
    REGULAR = 1
    SHORT = 2
    BURST = 3
    LONG = 4
    SHORT_LONG = 5
    SHORT_SHORT = 6
    BIG_PAUSE = 7

class KanoWand(WandBase):
    """A wand class to interact with the Kano wand"""

    def __init__(self, device_addr, name, bleak_loop):
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=1, y=0, z=0)
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 0.4
        self.name = name
        self._dev = bleak.BleakClient(device_addr)
        self._bleak_loop = bleak_loop
        self.position_raw = pyquaternion.Quaternion()
        
        print(f'Connecting to {self.name}...')
        connected = self._await_bleak(self._dev.connect())
        if not connected:
            print(f'Could not connect to {self.name}')
            return
        
        self._await_bleak(self._dev.start_notify(KANO_IO.QUATERNIONS_CHAR.value, self._handle_notification))
        self._await_bleak(self._dev.start_notify(KANO_IO.USER_BUTTON_CHAR.value, self._handle_notification))
        self.set_led(0, 0, 255)
        self.connected = True
        self.connected_time = time.time()
        print(f'Connected to {self.name}')

    def __repr__(self):
        return f'KanoWand(Name: {self.name}, Address: {self._dev.address})'
    
    def _await_bleak(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._bleak_loop).result()

    def _handle_notification(self, sender, data):
        if sender.uuid == KANO_IO.QUATERNIONS_CHAR.value:
            y = np.int16(np.uint16(int.from_bytes(data[0:2], byteorder='little'))) / 1000
            x = -1 * np.int16(np.uint16(int.from_bytes(data[2:4], byteorder='little'))) / 1000
            w = -1 * np.int16(np.uint16(int.from_bytes(data[4:6], byteorder='little'))) / 1000
            z = np.int16(np.uint16(int.from_bytes(data[6:8], byteorder='little'))) / 1000
            self.position_raw = pyquaternion.Quaternion(w=w, x=x, y=y, z=z)
        elif sender.uuid == KANO_IO.USER_BUTTON_CHAR.value:
            self.button = data[0] == 1
            self.reset_cal = True
            self.connected_time = time.time()

    def quit(self) -> None:
        if self.connected:
            pygame.event.post(pygame.event.Event(KANO_WAND_DISCONNECT, wand_name=self.name))
            self.connected = False
            self._await_bleak(self._dev.disconnect())
            print(f'Disconnected from {self.name}')
        
    def update_position(self) -> None:
        if not self.connected:
            return
        if not self.cal_offset or self.reset_cal:
            self.cal_offset = self.BASE_2.rotate(self.BASE_1.rotate(self.position_raw)).inverse
            self.reset_cal = False
        self.position = self.cal_offset * self.BASE_2.rotate(self.BASE_1.rotate(self.position_raw))

        tip_pos = self.position.rotate([1, 0, 0])[2]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append(tip_pos)
        new_speed = self.pos_queue[0] - self.pos_queue[-1]
        if self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD and self.callback:
            self.callback()
            self.vibrate(KANO_PATTERN.SHORT)
        self.prev_speed = new_speed

        # Auto disconnect after 10 minutes of not pressing any buttons
        if time.time() > self.connected_time + 600:
            self.quit()

    def vibrate(self, pattern=KANO_PATTERN.REGULAR):
        message = [pattern.value if isinstance(pattern, KANO_PATTERN) else pattern]
        self._await_bleak(self._dev.write_gatt_char(KANO_IO.VIBRATOR_CHAR.value, bytearray(message), response=True))

    def set_led(self, r: int, g: int, b: int, on=True):
        rgb = (((r & 248) << 8) + ((g & 252) << 3) + ((b & 248) >> 3))
        message = [1 if on else 0, rgb >> 8, rgb & 0xff]
        self._await_bleak(self._dev.write_gatt_char(KANO_IO.LED_CHAR.value, bytearray(message), response=True))

class KanoScanner:
    """A scanner class to connect to wands"""

    def __init__(self):
        self._bleak_loop = None
        self._bleak_thread = threading.Thread(target=self._run_bleak_loop, daemon=True)
        self._bleak_thread_ready = threading.Event()
        self._bleak_thread.start()
        self._bleak_thread_ready.wait()
        self.found_wands = {}

        self._scan_thread = threading.Thread(target=self._scan_thread, daemon=True)
        self._scan_event = threading.Event()
        self.scanning = False
        
    def _run_bleak_loop(self):
        self._bleak_loop = asyncio.new_event_loop()
        self._bleak_thread_ready.set()
        self._bleak_loop.run_forever()

    def start(self):
        if not self.scanning:
            print('Starting Kano Wand scanner')
            self.scanning = True
            self._scan_thread.start()

    def stop(self):
        if self.scanning:
            print('Stopping Kano Wand scanner')
            self.scanning = False
            self._scan_event.set()
            self._scan_thread.join()
    
    def _scan_thread(self):
        while self.scanning:
            new_wands = self.scan()
            for wand in new_wands:
                pygame.event.post(pygame.event.Event(KANO_WAND_CONNECT, wand=wand))
            self._scan_event.wait(5)

    def scan(self):
        for wand in list(self.found_wands):
            if not self.found_wands[wand].connected:
                del self.found_wands[wand]
        devices = asyncio.run_coroutine_threadsafe(bleak.BleakScanner.discover(timeout=2.0), self._bleak_loop).result()
        devices = [d for d in devices if d.name is not None and d.name.startswith("Kano-Wand") and d.name not in self.found_wands]
        new_wands = [KanoWand(d.address, d.name, self._bleak_loop) for d in devices]
        for wand in new_wands:
            self.found_wands[wand.name] = wand
        return new_wands
    

if __name__ == '__main__':
    wands = []

    kano_scanner = KanoScanner()
    wands.extend(kano_scanner.scan())
    
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
