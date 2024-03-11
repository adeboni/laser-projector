"""This module generates data for the lasers"""
from threading import Thread
import socket
import time
from laser_point import *
from laser_generators import *

class LaserServer:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, host_ip: str) -> None:
        if host_ip == '127.0.0.1':
            self.targets = [(host_ip, 8090 + i) for i in range(num_lasers)]
        else:
            self.targets = [(f'10.0.0.{10 + i}', 8090) for i in range(num_lasers)]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = Thread(target=self._server, daemon=True)
        self.server_running = False
        self.mode = 0
        self.num_lasers = num_lasers
        self.mode_list = {
            1: circle(num_lasers), 
            2: rainbow_circle(num_lasers),
            3: letters(num_lasers),
            4: images(num_lasers),
            5: spirograph(num_lasers),
            # 6: bouncing_ball(num_lasers)
        }

    def _server(self):
        PACKET_DELAY = 0.0258
        last_sent = 0
        seq = 0
        packet = None
        while self.server_running:
            if not self.mode in self.mode_list:
                continue

            if not packet:
                packet = [[seq] for _ in range(self.num_lasers)]
                for _ in range(170):
                    p = next(self.mode_list[self.mode])
                    for i in range(self.num_lasers):
                        packet[i].extend(p[i].get_bytes())
                seq = (seq + 1) % 255

            new_time = time.time()
            if new_time - last_sent > PACKET_DELAY:
                for i in range(self.num_lasers):
                    self.sock.sendto(bytearray(packet[i]), self.targets[i])
                last_sent = new_time
                packet = None
    
    def start_server(self) -> None:
        if not self.server.is_alive():
            print(f'Starting server targeting {self.targets}')
            self.server_running = True
            self.server.start()
            
    def stop_server(self) -> None:
        print('Stopping server')
        self.server_running = False
        while self.server.is_alive():
            pass

if __name__ == '__main__':
    import time
    import utilities
    if utilities.ping('10.0.0.2'):
        server = LaserServer(num_lasers=3, host_ip='10.0.0.2')
    else:
        server = LaserServer(num_lasers=3, host_ip='127.0.0.1')
    server.start_server()
    try:
        while True:
            for i in server.mode_list:
                server.mode = i
                time.sleep(5)
    except KeyboardInterrupt:
        server.stop_server()
