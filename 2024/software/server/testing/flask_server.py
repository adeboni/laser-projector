"""Flask server test"""
import time
from flask import Flask, Response
import numpy as np

app = Flask(__name__)

def _rainbow_circle() -> dict[int, tuple[list, list]]:
    """Generates a rainbow circle"""
    t = time.time() * 100
    phi = np.linspace(0, 360, 90) * np.pi / 180
    x = (np.sin(t * np.pi / 180) * 400 + 600) * np.sin(phi) + 2048
    y = (np.sin(t * np.pi / 180) * 400 + 600) * np.cos(phi) + 2048
    colors = (np.stack((np.cos(phi), np.cos(phi + 2 * np.pi / 3), np.cos(phi - 2 * np.pi / 3))).T + 1) * 127.5
    colors = [[int(c[0]), int(c[1]), int(c[2])] for c in colors]
    segments = [[(int(x1), int(y1)), (int(x2), int(y2))] for x1, x2, y1, y2 in zip(x, x[1:], y, y[1:])]
    return (segments, colors)

def xy_to_bytes(x, y) -> list[int]:
    """Converts two 12 bit values to three 8 bit values for sACN"""
    return [x >> 4, (x & 0xf) << 4 | y >> 8, y & 0xff]

@app.route('/laser_data/<int:num_points>/', methods = ['GET'])
def get_laser_data(num_points) -> Response:
    """Returns the next set of laser data"""
    return_buf = []
    segments, colors = _rainbow_circle()
    return_buf.extend(xy_to_bytes(*segments[0][0]))
    return_buf.extend([0, 0, 0])
    for s, c in zip([i[1] for i in segments], colors):
        return_buf.extend(xy_to_bytes(*s))
        return_buf.extend([c[0], c[1], c[2]])
    return Response(bytes(return_buf), mimetype='application/octet-stream')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8100)
