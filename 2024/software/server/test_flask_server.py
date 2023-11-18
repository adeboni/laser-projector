"""Flask server test"""
from threading import Thread
from queue import Queue
from flask import Flask, Response
from laser_point import *
from laser_generators import *

flask_app = Flask(__name__)

point_gen = rainbow_circle()
queue = Queue(1024)

@flask_app.route('/laser_data/<int:laser_id>/<int:num_points>/', methods = ['GET'])
def get_laser_data(laser_id: int, num_points: int) -> Response:
    """Returns the next set of laser data"""
    return_buf = []
    while len(return_buf) < num_points * 6:
        b = queue.get()
        if b is None:
            break
        return_buf.extend(b.get_bytes())
    return Response(bytes(return_buf), mimetype='application/octet-stream')

def producer(queue: Queue):
    while True:
        if not queue.full():
            queue.put(next(point_gen))

producer = Thread(target=producer, args=(queue,), daemon=True)
producer.start()

if __name__ == '__main__':
    flask_app.run(host='192.168.11.10', port=8100)
	#flask_app.run(host='127.0.0.1', port=8100)
