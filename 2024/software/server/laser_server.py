"""This module generates data for the lasers"""
from threading import Thread
from queue import Queue
from waitress import serve
from flask import Flask, Response, current_app
from laser_point import *
from laser_generators import *

class LaserServer:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, host_ip: str) -> None:
        self.mode = 0
        self.num_lasers = num_lasers
        self.mode_list = {1: circle(), 2: rainbow_circle()}

        self.flask_app = Flask(__name__)
        self.flask_app.queues = [Queue(8192) for _ in range(self.num_lasers)]
        #self.server = Thread(target=self.flask_app.run, kwargs={'host': host_ip, 'port': 8080, 'threaded': True}, daemon=True)
        self.server = Thread(target=lambda: serve(self.flask_app, host=host_ip, port=8080), daemon=True)
        self.gen = Thread(target=self.producer, args=(self.flask_app.queues,), daemon=True)
        
        @self.flask_app.route('/laser_data/<int:laser_id>/<int:num_points>/', methods = ['GET'])
        def get_laser_data(laser_id: int, num_points: int) -> Response:
            """Returns the next set of laser data"""
            if laser_id > len(current_app.queues):
                return Response(b'', mimetype='application/octet-stream')
            
            return_buf = []
            while len(return_buf) < num_points * 6:
                try:
                    point = current_app.queues[laser_id].get_nowait()
                    return_buf.extend(point.get_bytes())
                except:
                    break
            return Response(bytes(return_buf), mimetype='application/octet-stream')
			
        @self.flask_app.route('/')
        def index():
            return 'Laser server is running!'
    
    def start_server(self) -> None:
        if not self.server.is_alive():
            self.server.start()

    def start_generator(self) -> None:
        if not self.gen.is_alive():
            self.gen.start()

    def producer(self, queues: list[Queue]) -> None:
        while True:
            if self.mode in self.mode_list and not queues[0].full():
                queues[0].put(next(self.mode_list[self.mode]))

if __name__ == '__main__':
    import time
    server = LaserServer(num_lasers=3, host_ip='10.0.0.2')
    #server = LaserServer(num_lasers=3, host_ip='127.0.0.1')
    server.mode = 1
    server.start_generator()
    server.start_server()
    while True:
        server.mode = 0
        time.sleep(5)
        server.mode = 1
        time.sleep(5)
