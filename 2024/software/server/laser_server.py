"""This module generates data for the lasers"""

import socket
import time
import threading
import laser_generators
import utilities

class LaserServer:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, host_ip: str, wands=None) -> None:
        if host_ip == '127.0.0.1':
            self.targets = [(host_ip, 8090 + i) for i in range(num_lasers)]
        else:
            self.targets = [(f'10.0.0.{10 + i}', 8090) for i in range(num_lasers)]

        laser_generators.current_wands = wands
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = threading.Thread(target=self._server, daemon=True)
        self.server_running = False
        self.mode = 0
        self.num_lasers = num_lasers
        self.mode_list = {
            1: None, 
            2: laser_generators.audio_visualization(num_lasers),
            3: laser_generators.equations(num_lasers),
            4: laser_generators.spirograph(num_lasers),
            5: laser_generators.pong(num_lasers),
            6: laser_generators.drums_graphics(num_lasers),
            7: laser_generators.wand_drawing(num_lasers),
            8: None,
            9: laser_generators.calibration(num_lasers)
        }

    def _server(self):
        for target_ip, _ in self.targets:
            if not utilities.ping(target_ip):
                print(f'Could not ping {target_ip}!')
            
        PACKET_DELAY = 0.0258
        last_sent = 0
        seq = 0
        packet = None
        while self.server_running:
            if self.mode not in self.mode_list or self.mode_list[self.mode] is None:
                continue

            if not packet and (gen := self.mode_list[self.mode]):
                packet = [[seq] for _ in range(self.num_lasers)]
                for _ in range(170):
                    p = next(gen)
                    for i in range(self.num_lasers):
                        packet[i].extend(p[i].get_bytes())
                seq = (seq + 1) % 255

            new_time = time.time()
            if packet and new_time - last_sent > PACKET_DELAY:
                for i in range(self.num_lasers):
                    self.sock.sendto(bytearray(packet[i]), self.targets[i])
                last_sent = new_time
                packet = None
    
    def start(self) -> None:
        if not self.server_running:
            print(f'Starting laser server targeting {self.targets}')
            self.server_running = True
            self.server.start()
            
    def stop(self) -> None:
        if self.server_running:
            print('Stopping laser server')
            self.server_running = False
            self.server.join()

    def set_effect(self, effect) -> None:
        laser_generators.current_effect = effect

    def set_song(self, song) -> None:
        laser_generators.current_song = song

    def set_song_handler(self, song_handler) -> None:
        laser_generators.song_handler = song_handler

if __name__ == '__main__':
    if utilities.ping('10.0.0.2'):
        server = LaserServer(num_lasers=3, host_ip='10.0.0.2')
    else:
        server = LaserServer(num_lasers=3, host_ip='127.0.0.1')
    server.start()
    try:
        while True:
            for i in server.mode_list:
                server.mode = i
                time.sleep(5)
    except KeyboardInterrupt:
        server.stop()
