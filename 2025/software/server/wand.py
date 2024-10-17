"""Defines various Wand implementations"""

import colorsys
import pyquaternion
import sierpinski
import laser_point
import numpy as np
import time
import threading
import itertools
import pyaudio
import socket
import pyautogui

INT16_MIN = np.iinfo(np.int16).min
INT16_MAX = np.iinfo(np.int16).max
FADE_LENGTH = 6
FADE_OUT = np.linspace(1, 0, FADE_LENGTH)
FADE_IN = np.linspace(0, 1, FADE_LENGTH)
BUFFER_LIMIT = 10
PORT = 5005

class WandServer():
    def __init__(self, connected_callback=None, disconnected_callback=None) -> None:
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.udp_thread_running = False
        self.udp_thread = threading.Thread(target=self._udp_thread, daemon=True)
        self.audio_thread_running = False
        self.audio_thread = threading.Thread(target=self._audio_thread, daemon=True)
        self.stream = None
        self.buffer = {}
        self.prev_audio_data = {}
        self.buffering = {}
        self.wands = {}
        self.pa = pyaudio.PyAudio()

    @property
    def get_connected_wands(self):
        return [w for w in self.wands.values() if w.connected]

    def print_audio_output_devices(self) -> None:
        for i in range(self.pa.get_device_count()):
            device = self.pa.get_device_info_by_index(i)
            if device["maxOutputChannels"] > 0:
                print(i, device["name"])

    def start_audio_output(self, device_index) -> None:
        self.stream = self.pa.open(
            output=True,
            rate=16000,
            channels=1,
            format=pyaudio.paInt16,
            output_device_index=device_index,
            frames_per_buffer=1024
        )

        self.audio_thread_running = True
        self.audio_thread.start()

    def stop_audio_output(self) -> None:
        if self.audio_thread_running:
            self.audio_thread_running = False
            self.audio_thread.join()
            self.pa.close(self.stream)
            self.stream = None

    def start_udp(self) -> None:
        self.udp_thread_running = True
        self.udp_thread.start()

    def stop_udp(self) -> None:
        if self.udp_thread_running:
            self.udp_thread_running = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('127.0.0.1', PORT))
            sock.sendto(bytes([]), ('127.0.0.1', 5005))
            sock.close()
            self.udp_thread.join()

    def _udp_thread(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', PORT))

        while self.udp_thread_running:
            raw_data, addr = sock.recvfrom(4096)
            if len(raw_data) == 0:
                continue

            addr = addr[0]
            if addr not in self.wands:
                print(f"Found new wand at {addr}")
                self.wands[addr] = Wand(addr, self.connected_callback, self.disconnected_callback)
                self.buffer[addr] = []
                self.prev_audio_data[addr] = np.zeros(FADE_LENGTH)
                self.buffering[addr] = False

            data = np.frombuffer(raw_data, np.int16)
            seq_num_diff = data[0] - self.wands[addr].seq_num
            if seq_num_diff > -20 and seq_num_diff <= 0:
                self.wands[addr].seq_num = data[0]
                continue

            self.wands[addr].update_data(data)
            if self.audio_thread_running:
                self.buffer[addr].append(data[9:-2])
                if len(self.buffer[addr]) > BUFFER_LIMIT and self.buffering[addr]:
                    self.buffering[addr] = False

    def _audio_thread(self) -> None:
        while self.audio_thread_running:
            audio_buffer = []
            for addr in self.buffer:
                if not self.buffering[addr] and len(self.buffer[addr]) > 0:
                    curr_packet = self.buffer[addr].pop(0).astype(np.int32)
                    prev_packet = self.prev_audio_data[addr]
                    transition = prev_packet[-FADE_LENGTH:] * FADE_OUT + curr_packet[:FADE_LENGTH] * FADE_IN
                    audio_buffer.append(np.concatenate((transition, curr_packet[FADE_LENGTH:-FADE_LENGTH])))
                    self.prev_audio_data[addr] = curr_packet
                    if len(self.buffer[addr]) == 0:
                        self.buffering[addr] = True
            else:
                time.sleep(0.001)

            if len(audio_buffer) > 0 and self.stream is not None:
                data = [np.clip(sum(group), INT16_MIN, INT16_MAX) for group in itertools.zip_longest(*audio_buffer, fillvalue=0)]
                self.stream.write(np.array(data).astype(np.int16).tobytes())

class Wand:
    def __init__(self, address=None, connected_callback=None, disconnected_callback=None) -> None:
        self.address = address
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback

        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 6
        self.TIME_KEEPOUT = 0.2
        self.pos_queue = []
        self.prev_speed = 0
        self.last_angle = 0

        self.position = pyquaternion.Quaternion()
        self.impact_callback = None
        self.impact_time = time.time()
        self.button = False
        self.button_pressed_time = None
        self.plugged_in = False
        self.charged = False
        self.battery_volts = 0
        self.connected = True
        self.seq_num = 0

        self.last_update = time.time()
        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self.watchdog_thread.start()
        if self.connected_callback:
            self.connected_callback(self)

    def _watchdog(self) -> None:
        while True:
            time.sleep(1)
            if time.time() > self.last_update + 10:
                if self.connected:
                    self.connected = False
                    if self.disconnected_callback:
                        self.disconnected_callback(self.address)

    def update_data(self, udp_data) -> None:
        self.last_update = time.time()
        self.seq_num = udp_data[0]
        self.plugged_in = udp_data[1] == 1
        self.charged = udp_data[2] == 1
        self.battery_volts = udp_data[3] / 4095 * 3.7
        self.update_button_data(udp_data[4] == 1)
        self.position = pyquaternion.Quaternion((udp_data[5:9] - 16384) / 16384)
        if self.check_for_impact() and self.impact_callback and time.time() - self.impact_time > self.TIME_KEEPOUT:
            self.impact_callback()
            self.impact_time = time.time()
        if not self.connected:
            self.connected = True
            if self.connected_callback:
                self.connected_callback(self)

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
            r = np.interp(abs(self.get_rotation_angle() - 180), [0, 180], [0, 1])
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
        if len(self.pos_queue) > self.POS_QUEUE_LIMIT:
            self.pos_queue.pop(0)
        tip_pos = self.position.rotate(sierpinski.wand_vector)
        self.pos_queue.append((tip_pos, time.time()))
        d = np.linalg.norm(self.pos_queue[-1][0] - self.pos_queue[0][0])
        t = self.pos_queue[-1][1] - self.pos_queue[0][1]
        if t < 0.01:
            return False
        new_speed = d / t
        result = self.prev_speed > self.SPEED_THRESHOLD and new_speed < self.SPEED_THRESHOLD
        self.prev_speed = new_speed
        return result

    def update_button_data(self, pressed: bool) -> None:
        if not self.button and pressed and self.impact_callback:
            self.impact_callback()
        self.button = pressed
        if self.button_pressed_time and time.time() - self.button_pressed_time > 2:
            sierpinski.calibrate_wand_position(self.position)
        if not self.button:
            self.button_pressed_time = None
        elif self.button_pressed_time is None:
            self.button_pressed_time = time.time()


class WandSimulator(Wand):
    def __init__(self) -> None:
        super().__init__()
        self.screen_width, self.screen_height = pyautogui.size()
        self.connected = False
        self.notify_thread = threading.Thread(target=self._notify, daemon=True)
        self._notify_event = threading.Event()
        self.connect()

    def __repr__(self) -> str:
        return 'WandSimulator()'

    def connect(self) -> None:
        if not self.connected:
            self.connected = True
            self.notify_thread.start()

    def disconnect(self) -> None:
        if self.connected:
            self.connected = False
            self._notify_event.set()
            self.notify_thread.join()

    def _notify(self) -> None:
        while self.connected:
            self.last_update = time.time()
            mouse = pyautogui.position()
            z = np.interp(mouse.x, [0, self.screen_width], [1, -1])
            x = np.interp(mouse.y, [0, self.screen_height], [-1, 1])
            self.position = pyquaternion.Quaternion(w=1, x=x, y=0, z=0) * pyquaternion.Quaternion(w=1, x=0, y=0, z=z)
            if self.check_for_impact() and self.impact_callback:
                self.impact_callback()
            self._notify_event.wait(0.02)

    def press_button(self, pressed: bool) -> None:
        self.update_button_data(pressed)



if __name__ == '__main__':
    ws = WandServer()
    ws.start_udp()
    #ws.start_audio_output(4)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        ws.stop_audio_output()
        ws.stop_udp()
