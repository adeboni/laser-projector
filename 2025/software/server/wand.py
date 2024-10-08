"""Defines various Wand implementations"""

import enum
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

class AddressState(enum.Enum):
    OPEN = 1
    CLOSED = 2


class WandServer():
    def __init__(self, connected_callback=None, disconnected_callback=None) -> None:
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
        self.tcp_thread_running = False
        self.tcp_thread = threading.Thread(target=self._tcp_thread, daemon=True)
        self.audio_thread_running = False
        self.audio_thread = threading.Thread(target=self._audio_thread, daemon=True)
        self.stream = None
        self.addresses = {}
        self.buffer = {}
        self.prev_audio_data = {}
        self.buffering = {}
        self.wands = {}
        self.pa = pyaudio.PyAudio()

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

    def start_tcp(self) -> None:
        self.tcp_thread_running = True
        self.tcp_thread.start()

    def stop_tcp(self) -> None:
        if self.tcp_thread_running:
            self.tcp_thread_running = False
            sock = socket.socket()
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect(('127.0.0.1', PORT))
            sock.close()
            self.tcp_thread.join()

    def _tcp_thread(self) -> None:
        sock = socket.socket()
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind(('0.0.0.0', PORT))
        sock.listen(5)

        while self.tcp_thread_running:
            print('Waiting for wand TCP connection...')
            conn, addr = sock.accept()
            print(f'Connected to wand at {addr}')

            if addr not in self.wands:
                self.wands[addr] = Wand(addr)
            self.wands[addr].connected = True
            if self.connected_callback:
                self.connected_callback(self.wands[addr])
            self.buffer[addr] = []
            self.prev_audio_data[addr] = np.zeros(FADE_LENGTH)
            self.buffering[addr] = False
            self.addresses[addr] = AddressState.OPEN

            thread = threading.Thread(target=self._read_data_from_socket, args=(conn, addr), daemon=True)
            thread.start()

    def _try_parse_buffer(self, tcp_buffer, addr) -> int:
        for i in range(1, len(tcp_buffer)):
            if tcp_buffer[i] == -21846 and tcp_buffer[i-1] == -21846:
                data = tcp_buffer[:i-2]
                self.wands[addr].update_data(data)
                if self.audio_thread_running:
                    self.buffer[addr].append(data[8:])
                    if len(self.buffer[addr]) > BUFFER_LIMIT and self.buffering[addr]:
                        self.buffering[addr] = False
                return i + 1
        return None

    def _read_data_from_socket(self, conn, addr) -> None:
        tcp_buffer = None
        while self.tcp_thread_running:
            raw_data = conn.recv(4096)
            if raw_data == b"":
                print(f"Lost connection from wand at {addr}")
                self.addresses[addr] = AddressState.CLOSED
                self.wands[addr].connected = False
                if self.disconnected_callback:
                    self.disconnected_callback(addr)
                break
            
            if tcp_buffer is None:
                tcp_buffer = np.frombuffer(raw_data, np.int16)
            else:
                tcp_buffer = np.concatenate((tcp_buffer, np.frombuffer(raw_data, np.int16)))
            if (start_index := self._try_parse_buffer(tcp_buffer, addr)):
                tcp_buffer = tcp_buffer[start_index:]

    def _transition_audio_data(self, x, y) -> np.array:
        transition = x[-FADE_LENGTH:] * FADE_OUT + y[:FADE_LENGTH] * FADE_IN
        return np.concatenate((transition, y[FADE_LENGTH:-FADE_LENGTH]))

    def _audio_thread(self) -> None:
        while self.audio_thread_running:
            audio_buffer = []
            for addr in [a for a in self.addresses if self.addresses[a] != AddressState.CLOSED]:
                if not self.buffering[addr] and len(self.buffer[addr]) > 0:
                    curr_packet = self.buffer[addr].pop(0).astype(np.int32)
                    prev_packet = self.prev_audio_data[addr]
                    audio_buffer.append(self._transition_audio_data(prev_packet, curr_packet))
                    self.prev_audio_data[addr] = curr_packet
                    if len(self.buffer[addr]) == 0:
                        self.buffering[addr] = True
            else:
                time.sleep(0.001)

            if len(audio_buffer) > 0 and self.stream is not None:
                data = [np.clip(sum(group), INT16_MIN, INT16_MAX) for group in itertools.zip_longest(*audio_buffer, fillvalue=0)]
                self.stream.write(np.array(data).astype(np.int16).tobytes())



class Wand:
    def __init__(self, address=None) -> None:
        self.POS_QUEUE_LIMIT = 5
        self.SPEED_THRESHOLD = 6
        self.min_x, self.max_x, self.min_y, self.max_y = sierpinski.get_laser_min_max_interior()
        self.position = pyquaternion.Quaternion()
        self.pos_queue = []
        self.prev_speed = 0
        self.cal_offset = None
        self.reset_cal = False
        self.last_angle = 0
        self.last_update = time.time()
        self.impact_callback = None
        self.button = False
        self.button_pressed_time = None
        self.address = address
        self.plugged_in = False
        self.charged = False
        self.battery_volts = 0
        self.connected = True

    def update_data(self, tcp_data) -> None:
        self.plugged_in = tcp_data[0] == 1
        self.charged = tcp_data[1] == 1
        self.battery_volts = tcp_data[2] / 4095 * 3.7
        self.update_button_data(tcp_data[3] == 1)
        self.position = pyquaternion.Quaternion((tcp_data[4:8] - 16384) / 16384)
        if self.check_for_impact() and self.impact_callback:
            self.impact_callback()

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

    def update_button_data(self, pressed: bool) -> None:
        self.last_update = time.time()
        if not self.button and pressed and self.impact_callback:
            self.impact_callback()
        self.button = pressed
        if self.button_pressed_time and time.time() - self.button_pressed_time > 2:
            self.reset_cal = True
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
            mouse = pyautogui.position()
            x = np.interp(mouse.x, [0, self.screen_width], [1, -1])
            y = np.interp(mouse.y, [0, self.screen_height], [-1, 1])
            self.position = pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                          * pyquaternion.Quaternion(w=1, x=0, y=y, z=0) \
                          * pyquaternion.Quaternion(w=1, x=0, y=0, z=x) \
                          * pyquaternion.Quaternion(w=1, x=0, y=0, z=x)
            if self.check_for_impact() and self.impact_callback:
                self.impact_callback()
            self._notify_event.wait(0.02)

    def press_button(self, pressed: bool) -> None:
        self.update_button_data(pressed)



if __name__ == '__main__':
    ws = WandServer()
    ws.start_tcp()
    #ws.start_audio_output(4)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        ws.stop_audio_output()
        ws.stop_tcp()