"""Defines various Wand implementations"""

import enum
import colorsys
import pyquaternion
import sierpinski
import laser_point
import numpy as np
import pyautogui
import time
import bleak
import threading
import asyncio

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
        self._bleak_loop = None
        
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
    
    def _await_bleak(self, coro):
        try:
            return asyncio.run_coroutine_threadsafe(coro, self._bleak_loop).result()
        except Exception as ex:
            print(f'Bleak error! {type(ex).__name__} {ex}')
        
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
    USER_BUTTON_CHAR = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    QUATERNIONS_CHAR = '64a70002-f691-4b93-a6f4-0968f5b648f8'

class MathCampWand(WandBase):
    """A wand class to interact with the Math Camp wand"""

    def __init__(self, device, bleak_loop, disconnected_callback=None):
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=0, y=0, z=-1)
        self.device = bleak.BleakClient(device)
        self._bleak_loop = bleak_loop
        self.connected = False
        self.disconnected_callback = disconnected_callback
        
        print(f'Connecting to {self.device.name} ({self.device.address})...')
        if not self._await_bleak(self.device.connect()):
            print(f'Could not connect to {self.name}')
            return
        
        self._await_bleak(self.device.start_notify(KANO_IO.QUATERNIONS_CHAR.value, self._handle_quaternion))
        self._await_bleak(self.device.start_notify(KANO_IO.USER_BUTTON_CHAR.value, self._handle_button))
        self.connected = True
        self.start_watchdog()
        print(f'Connected to {self.device.name}')

    def __repr__(self):
        return f'MathCampWand(Name: {self.device.name}, Address: {self.device.address})'
    
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
            name = self.device.name
            self.connected = False
            self.device.disconnect()
            print(f'Disconnected from {name}')   
            if self.disconnected_callback:
                self.disconnected_callback(name)          
        

class KANO_IO(enum.Enum):
    QUATERNIONS_CHAR = '64a70002-f691-4b93-a6f4-0968f5b648f8'
    USER_BUTTON_CHAR = '64a7000d-f691-4b93-a6f4-0968f5b648f8'
    VIBRATOR_CHAR    = '64a70008-f691-4b93-a6f4-0968f5b648f8'
    LED_CHAR         = '64a70009-f691-4b93-a6f4-0968f5b648f8'

class KANO_PATTERN(enum.Enum):
    REGULAR     = 1
    SHORT       = 2
    BURST       = 3
    LONG        = 4
    SHORT_LONG  = 5
    SHORT_SHORT = 6
    BIG_PAUSE   = 7

class KanoWand(WandBase):
    """A wand class to interact with the Kano wand"""

    def __init__(self, device, bleak_loop, disconnected_callback=None):
        super().__init__()
        self.BASE_1 = pyquaternion.Quaternion(w=1, x=0, y=-1, z=0)
        self.BASE_2 = pyquaternion.Quaternion(w=1, x=1, y=0, z=0)
        self.device = bleak.BleakClient(device)
        self._bleak_loop = bleak_loop
        self.connected = False
        self.disconnected_callback = disconnected_callback
        
        print(f'Connecting to {self.device.name} ({self.device.address})...')
        if not self._await_bleak(self.device.connect()):
            print(f'Could not connect to {self.name}')
            return
        
        self._await_bleak(self.device.start_notify(KANO_IO.QUATERNIONS_CHAR.value, self._handle_quaternion))
        self._await_bleak(self.device.start_notify(KANO_IO.USER_BUTTON_CHAR.value, self._handle_button))
        self.set_led(0, 0, 255)
        self.connected = True
        self.start_watchdog()
        print(f'Connected to {self.device.name}')

    def __repr__(self):
        return f'KanoWand(Name: {self.device.name}, Address: {self.device.address})'
    
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
            name = self.device.name
            self.connected = False
            self.device.disconnect()
            print(f'Disconnected from {name}')
            if self.disconnected_callback:
                self.disconnected_callback(name)
        
    def vibrate(self, pattern):
        message = [pattern.value if isinstance(pattern, KANO_PATTERN) else pattern]
        self._await_bleak(self.device.write_gatt_char(KANO_IO.VIBRATOR_CHAR.value, bytearray(message), response=True))

    def set_led(self, r: int, g: int, b: int, on=True):
        rgb = (((r & 248) << 8) + ((g & 252) << 3) + ((b & 248) >> 3))
        message = [1 if on else 0, rgb >> 8, rgb & 0xff]
        self._await_bleak(self.device.write_gatt_char(KANO_IO.LED_CHAR.value, bytearray(message), response=True))

class BLEScanner:
    """A scanner class to connect to wands"""

    def __init__(self, connected_callback=None, disconnected_callback=None):
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self._bleak_loop = None
        self._bleak_thread = threading.Thread(target=self._run_bleak_loop, daemon=True)
        self._bleak_thread_ready = threading.Event()
        self._bleak_thread.start()
        self._bleak_thread_ready.wait()
        self.found_wands = {}

        self.scan_thread = threading.Thread(target=self._scan_thread, daemon=True)
        self._scan_event = threading.Event()
        self.scanning = False
        
    def _run_bleak_loop(self):
        self._bleak_loop = asyncio.new_event_loop()
        self._bleak_thread_ready.set()
        self._bleak_loop.run_forever()

    def start(self):
        if not self.scanning:
            print('Starting wand scanner')
            self.scanning = True
            self.scan_thread.start()

    def stop(self):
        if self.scanning:
            print('Stopping wand scanner')
            self.scanning = False
            self._scan_event.set()
            self.scan_thread.join()
    
    def _scan_thread(self):
        while self.scanning:
            new_wands = self.scan()
            if self.connected_callback:
                for wand in new_wands:
                    self.connected_callback(wand)
            self._scan_event.wait(5)

    def scan(self):
        for wand in list(self.found_wands):
            if not self.found_wands[wand].connected:
                del self.found_wands[wand]

        devices = asyncio.run_coroutine_threadsafe(bleak.BleakScanner.discover(timeout=2.0), self._bleak_loop).result()
        devices = [d for d in devices if d.name is not None and d.name not in self.found_wands]

        kano_wands = [KanoWand(d, self._bleak_loop, self.disconnected_callback) for d in devices if d.name.startswith("Kano-Wand")]
        kano_wands = [w for w in kano_wands if wand.connected]

        math_camp_wands = [MathCampWand(d, self._bleak_loop, self.disconnected_callback) for d in devices if d.name.startswith("Math Camp Wand")]
        math_camp_wands = [w for w in math_camp_wands if wand.connected]

        new_wands = [*kano_wands, *math_camp_wands]
        for wand in new_wands:
            self.found_wands[wand.name] = wand
        return new_wands

if __name__ == '__main__':
    ble_scanner = BLEScanner()
    wands = ble_scanner.scan()
    print('Found wands:', wands)
