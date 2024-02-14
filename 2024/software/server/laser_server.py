"""This module generates data for the lasers"""
from threading import Thread
from queue import Queue
from waitress import serve
from flask import Flask, Response
from laser_point import *
from laser_generators import *

class LaserServer:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, host_ip: str) -> None:
        self.max_queue_size = 4096
        self.host_ip = host_ip
        self.mode = 0
        self.num_lasers = num_lasers
        self.mode_list = {
            1: circle(num_lasers), 
            2: rainbow_circle(num_lasers),
            3: letters(num_lasers),
            4: images(num_lasers),
            5: spirograph(num_lasers)
        }

        self.flask_app = Flask(__name__)
        self.queues = [Queue(self.max_queue_size) for _ in range(self.num_lasers)]
        self.server = Thread(target=lambda: serve(self.flask_app, host=host_ip, port=8080), daemon=True)
        self.gen = Thread(target=self.producer, daemon=True)
        
        @self.flask_app.route('/laser_data/<int:laser_id>/<int:num_points>/', methods = ['GET'])
        def get_laser_data(laser_id: int, num_points: int) -> Response:
            """Returns the next set of laser data"""
            if laser_id > len(self.queues):
                return Response(b'', mimetype='application/octet-stream')
            
            return_buf = []
            while len(return_buf) < num_points * 6:
                try:
                    point = self.queues[laser_id].get_nowait()
                    return_buf.extend(point.get_bytes())
                except:
                    return_buf.extend([0, 0, 0, 0, 0, 0])
            return Response(bytes(return_buf), mimetype='application/octet-stream')
            
        @self.flask_app.route('/')
        def index():
            return 'Laser server is running!'
    
    def start_server(self) -> None:
        if not self.server.is_alive():
            print(f'Starting server at {self.host_ip}')
            self.server.start()

    def start_generator(self) -> None:
        if not self.gen.is_alive():
            self.gen.start()

    def producer(self) -> None:
        while True:
            if self.mode not in self.mode_list or all(q.full() for q in self.queues):
                continue
            min_size = min(q.qsize() for q in self.queues)
            if not any(q.full() for q in self.queues) or min_size < self.max_queue_size / 2:
                for p in next(self.mode_list[self.mode]):
                    if not self.queues[p.id].full():
                        self.queues[p.id].put(p)

if __name__ == '__main__':
    import time
    import utilities
    if utilities.ping('10.0.0.2'):
        server = LaserServer(num_lasers=3, host_ip='10.0.0.2')
    else:
        server = LaserServer(num_lasers=3, host_ip='127.0.0.1')
    server.start_generator()
    server.start_server()
    while True:
        for i in server.mode_list:
            server.mode = i
            time.sleep(5)
