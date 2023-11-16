"""Flask server test"""
from threading import Thread
from queue import Queue
from flask import Flask, Response
import numpy as np

app = Flask(__name__)

def _rainbow_circle() -> tuple[list, list]:
    """Generates a rainbow circle"""
    d = 0
    while True:
        x = 1000 * np.sin(d * np.pi / 180) + 2048
        y = 1000 * np.cos(d * np.pi / 180) + 2048
        rgb = [d % 255, (d + 60) % 255, (d + 120) % 255]
        yield ([int(x), int(y)], rgb)
        d = (d + 8) % 360

point_gen = _rainbow_circle()
queue = Queue(1024)

def xy_to_bytes(x: int, y: int) -> list[int]:
    """Converts two 12 bit values to three 8 bit values"""
    return [x >> 4, (x & 0xf) << 4 | y >> 8, y & 0xff]

@app.route('/laser_data/<int:num_points>/', methods = ['GET'])
def get_laser_data(num_points: int) -> Response:
    """Returns the next set of laser data"""
    return_buf = []
    while len(return_buf) < num_points * 6:
        b = queue.get()
        if b is None:
            break
        return_buf.append(b)
    return Response(bytes(return_buf), mimetype='application/octet-stream')

def producer(queue: Queue):
    while True:
        if not queue.full():
            point, rgb = next(point_gen)
            for b in xy_to_bytes(*point):
                queue.put(b)
            for b in rgb:
                queue.put(b)

producer = Thread(target=producer, args=(queue,), daemon=True)
producer.start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8100)
