"""Defines various Wand implementations"""

import enum
import colorsys
import pygame
import pyquaternion
import sierpinski
import laser_point
import numpy as np
import pyautogui
import time
import simplepyble
import threading

BLE_WAND_CONNECT = pygame.USEREVENT + 1
BLE_WAND_DISCONNECT = pygame.USEREVENT + 2

class WandBase:
    def __init__(self) -> None:
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 6
        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.position = pyquaternion.Quaternion()
        self.callback = None
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None
        self.reset_cal = False
        self.last_angle = 0
        self.last_update = time.time()

        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self._watchdog_event = threading.Event()
        self.watchdog_running = False
        
    def start_watchdog(self) -> None:
        if not self.watchdog_running:
            self.last_update = time.time()
            self.watchdog_running = True
            self.watchdog_thread.start()

    def stop_watchdog(self) -> None:
        if self.watchdog_running:
            self.watchdog_running = False
            self._watchdog_event.set()

    def _watchdog(self) -> None:
        while self.watchdog_running:
            self._watchdog_event.wait(1)
            if time.time() > self.last_update + 30:
                self.disconnect()

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
        
    def check_for_impact(self) -> bool:
        tip_pos = self.position.rotate([1, 0, 0])[2]
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        self.pos_queue.append((tip_pos, time.time()))
        d = self.pos_queue[-1][0] - self.pos_queue[0][0]
        t = self.pos_queue[-1][1] - self.pos_queue[0][1]
        if t < 0.01:
            return False
        new_speed = -d / t
        result = self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD
        self.prev_speed = new_speed
        return result
        
class WandSimulator(WandBase):
    def __init__(self) -> None:
        super().__init__()
        self.screen_width, self.screen_height = pyautogui.size()
        self.connected = True
        self.notify_thread = threading.Thread(target=self._notify, daemon=True)
        self._notify_event = threading.Event()
        self.notify_thread.start()

    def __repr__(self):
        return 'WandSimulator()'

    def disconnect(self) -> None:
        self.connected = False
        self._notify_event.set()
        self.notify_thread.join()

    def _notify(self) -> None:
        while self.connected:
            mouse = pyautogui.position()
            x = np.interp(mouse.x, [0, self.screen_width], [1, -1])
            y = np.interp(mouse.y, [0, self.screen_height], [-1, 1])
            self.position = pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                          * pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                          * pyquaternion.Quaternion(w=1, x=0, y=0, z=x) \
                          * pyquaternion.Quaternion(w=1, x=0, y=0, z=x)
            self._notify_event.wait(0.02)
            if self.check_for_impact() and self.callback:
                self.callback()

class MATH_CAMP_WAND_IO(enum.Enum):
    SERVICE_CHAR     = '64a70011-f691-4b93-a6f4-0968f5b648f8'
    USER_BUTTON_CHAR = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_CHAR = '64a70002-f691-4b93-a6f4-0968f5b648f8'

class MathCampWand(WandBase):
    """A wand class to interact with the Math Camp wand"""

    def __init__(self, device):
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=0, y=0, z=-1)
        self.device = device
        self.connected = False
        
        print(f'Connecting to {self.device.identifier()} ({self.device.address()})...')
        try:
            self.device.connect()
        except:
            print(f'Could not connect to {self.device.identifier()}')
            return
        
        self.device.notify(MATH_CAMP_WAND_IO.SERVICE_CHAR.value, MATH_CAMP_WAND_IO.QUATERNIONS_CHAR.value, self._handle_quaternion)
        self.device.notify(MATH_CAMP_WAND_IO.SERVICE_CHAR.value, MATH_CAMP_WAND_IO.USER_BUTTON_CHAR.value, self._handle_button)
        self.connected = True
        self.start_watchdog()
        print(f'Connected to {self.device.identifier()}')

    def __repr__(self):
        return f'MathCampWand(Name: {self.device.identifier()}, Address: {self.device.address()})'
    
    def _handle_quaternion(self, data):
        self.last_update = time.time()
        x = (np.int16(np.uint16(int.from_bytes(data[0:2], byteorder='little'))) - 16384) / 16384
        y = (np.int16(np.uint16(int.from_bytes(data[2:4], byteorder='little'))) - 16384) / 16384
        z = (np.int16(np.uint16(int.from_bytes(data[4:6], byteorder='little'))) - 16384) / 16384
        w = (np.int16(np.uint16(int.from_bytes(data[6:8], byteorder='little'))) - 16384) / 16384
        position_raw = pyquaternion.Quaternion(w=w, x=x, y=y, z=z)

        if not self.cal_offset or self.reset_cal:
            self.cal_offset = self.BASE_2.rotate(self.BASE_1.rotate(position_raw)).inverse
            self.reset_cal = False
        self.position = self.cal_offset * self.BASE_2.rotate(self.BASE_1.rotate(position_raw))

        if self.check_for_impact() and self.callback:
            self.callback()

    def _handle_button(self, data):
        self.last_update = time.time()
        self.button = data[0] == 1
        self.reset_cal = True

    def disconnect(self) -> None:
        if self.connected:
            self.stop_watchdog()
            name = self.device.identifier()
            self.connected = False
            self.device.disconnect()
            print(f'Disconnected from {name}')    
            #pygame.event.post(pygame.event.Event(BLE_WAND_DISCONNECT, wand_name=name))            
        

class KANO_IO(enum.Enum):
    QUAT_SERVICE_CHAR     = '64a70011-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_CHAR      = '64a70002-f691-4b93-a6f4-0968f5b648f8'
    BUTTON_SERVICE_CHAR   = '64a70012-f691-4b93-a6f4-0968f5b648f8'
    USER_BUTTON_CHAR      = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    VIBRATOR_SERVICE_CHAR = '64a70012-f691-4b93-a6f4-0968f5b648f8'
    VIBRATOR_CHAR         = '64a70008-f691-4b93-a6f4-0968f5b648f8'
    LED_SERVICE_CHAR      = '64a70012-f691-4b93-a6f4-0968f5b648f8'
    LED_CHAR              = '64a70009-f691-4b93-a6f4-0968f5b648f8'

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

    def __init__(self, device):
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=1, y=0, z=0)
        self.device = device
        self.connected = False
        
        print(f'Connecting to {self.device.identifier()} ({self.device.address()})...')
        try:
            self.device.connect()
        except:
            print(f'Could not connect to {self.device.identifier()}')
            return
        
        self.device.notify(KANO_IO.BUTTON_SERVICE_CHAR.value, KANO_IO.USER_BUTTON_CHAR.value, self._handle_button)
        self.device.notify(KANO_IO.QUAT_SERVICE_CHAR.value, KANO_IO.QUATERNIONS_CHAR.value, self._handle_quaternion)
        self.set_led(0, 0, 255)
        self.connected = True
        self.start_watchdog()
        print(f'Connected to {self.device.identifier()}')

    def __repr__(self):
        return f'KanoWand(Name: {self.device.identifier()}, Address: {self.device.address()})'
    
    def _handle_quaternion(self, data):
        print('quat', data)
        self.last_update = time.time()
        y = np.int16(np.uint16(int.from_bytes(data[0:2], byteorder='little'))) / 1000
        x = -1 * np.int16(np.uint16(int.from_bytes(data[2:4], byteorder='little'))) / 1000
        w = -1 * np.int16(np.uint16(int.from_bytes(data[4:6], byteorder='little'))) / 1000
        z = np.int16(np.uint16(int.from_bytes(data[6:8], byteorder='little'))) / 1000
        position_raw = pyquaternion.Quaternion(w=w, x=x, y=y, z=z)

        if not self.cal_offset or self.reset_cal:
            self.cal_offset = self.BASE_2.rotate(self.BASE_1.rotate(position_raw)).inverse
            self.reset_cal = False
        self.position = self.cal_offset * self.BASE_2.rotate(self.BASE_1.rotate(position_raw))

        if self.check_for_impact() and self.callback:
            self.callback()
            self.vibrate(KANO_PATTERN.SHORT)

    def _handle_button(self, data):
        print('button', data)
        self.last_update = time.time()
        self.button = data[0] == 1
        self.reset_cal = True

    def disconnect(self) -> None:
        if self.connected:
            self.stop_watchdog()
            name = self.device.identifier()
            self.connected = False
            self.device.disconnect()
            print(f'Disconnected from {name}')
            #pygame.event.post(pygame.event.Event(BLE_WAND_DISCONNECT, wand_name=name))
        
    def vibrate(self, pattern):
        message = [pattern.value if isinstance(pattern, KANO_PATTERN) else pattern]
        self.device.write_request(KANO_IO.VIBRATOR_SERVICE_CHAR.value, KANO_IO.VIBRATOR_CHAR.value, bytes(message))

    def set_led(self, r: int, g: int, b: int, on=True):
        rgb = (((r & 248) << 8) + ((g & 252) << 3) + ((b & 248) >> 3))
        message = [1 if on else 0, rgb >> 8, rgb & 0xff]
        self.device.write_request(KANO_IO.LED_SERVICE_CHAR.value, KANO_IO.LED_CHAR.value, bytes(message))

class BLEScanner:
    """A scanner class to connect to wands"""

    def __init__(self):
        self.found_wands = {}
        self.adapter = simplepyble.Adapter.get_adapters()[0]
        self.adapter.set_callback_on_scan_found(self._device_found)
        self.scanning = False

    def _device_found(self, device):
        print(device.identifier())
        name = device.identifier()
        if name is not None:
            if name in self.found_wands and self.found_wands[name].connected:
                return
            wand = None
            if name.startswith('Kano-Wand'):
                wand = KanoWand(device)
            elif name.startswith('Math Camp Wand'):
                wand = MathCampWand(device)
            if wand is not None and wand.connected:
                self.found_wands[name] = wand
                #pygame.event.post(pygame.event.Event(BLE_WAND_CONNECT, wand=wand))
        
    def start(self):
        if not self.scanning:
            print('Starting wand scanner')
            self.scanning = True
            self.adapter.scan_start()

    def stop(self):
        if self.scanning:
            print('Stopping wand scanner')
            self.scanning = False
            self.adapter.scan_stop()

if __name__ == '__main__':
    ble_scanner = BLEScanner()
    ble_scanner.start()
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        ble_scanner.stop()
    print('Found wands:', ble_scanner.found_wands)
