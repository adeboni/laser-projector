"""This module generates data for the lasers"""

import socket
import time
import threading
import laser_generators
import utilities

class LaserServer:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, host_ip: str) -> None:
        if host_ip == '127.0.0.1':
            self.targets = [(host_ip, 8090 + i) for i in range(num_lasers)]
        else:
            self.targets = [(f'10.0.0.{10 + i}', 8090) for i in range(num_lasers)]

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
            6: laser_generators.wand_drawing(num_lasers),
            7: laser_generators.wand_drawing(num_lasers),
            8: laser_generators.drums(num_lasers),
            9: laser_generators.calibration(num_lasers)
        }

    def _server(self):
        PACKET_DELAY = 0.0258
        last_sent = 0
        seq = 0
        packet = None
        while self.server_running:
            if self.mode not in self.mode_list or self.mode_list[self.mode] is None:
                continue

            if not packet:
                packet = [[seq] for _ in range(self.num_lasers)]
                gen = self.mode_list[self.mode]
                if gen is None:
                    continue
                for _ in range(170):
                    p = next(gen)
                    for i in range(self.num_lasers):
                        packet[i].extend(p[i].get_bytes())
                seq = (seq + 1) % 255

            new_time = time.time()
            if new_time - last_sent > PACKET_DELAY:
                for i in range(self.num_lasers):
                    self.sock.sendto(bytearray(packet[i]), self.targets[i])
                last_sent = new_time
                packet = None
    
    def start(self) -> None:
        if not self.server.is_alive():
            print(f'Starting laser server targeting {self.targets}')
            for target_ip, _ in self.targets:
                utilities.ping(target_ip)
            self.server_running = True
            self.server.start()
            
    def stop(self) -> None:
        print('Stopping laser server')
        self.server_running = False
        while self.server.is_alive():
            pass

    def set_effect(self, effect) -> None:
        laser_generators.current_effect_end_time = time.time() + effect.length_s / 6

    def set_song(self, song) -> None:
        laser_generators.current_song = song
        
    def set_wands(self, wands) -> None:
        laser_generators.current_wands = wands

if __name__ == '__main__':
    import time
    import utilities
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
