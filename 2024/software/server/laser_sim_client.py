"""This module simulates laser outputs"""

import socket
import threading
import traceback
from matplotlib import pyplot as plt
from matplotlib import collections as mc
from matplotlib import animation
from laser_point import *
import sierpinski

NUM_LASERS = 3
MAX_POINTS = 200

segments = [[LaserSegment(i)] for i in range(NUM_LASERS)]

def _laser_thread(laser_index):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 8090 + laser_index))
        curr_seq = 0
        while True:
            data, _ = sock.recvfrom(1024)
            raw_bytes = list(data)
            seq = raw_bytes.pop(0)
            if seq != (curr_seq + 1) % 255:
                curr_seq = seq
                continue
            curr_seq = seq

            for i in range(0, len(raw_bytes), 6):
                chunk = raw_bytes[i:i + 6]
                if len(chunk) != 6:
                    break
                new_point = LaserPoint.from_bytes(laser_index, chunk)
                segments[laser_index].append(LaserSegment(laser_index, segments[laser_index][-1].end, new_point, 
                                                        [new_point.r / 255, new_point.g / 255, new_point.b / 255]))
                while len(segments[laser_index]) > MAX_POINTS:
                    segments[laser_index].pop(0)
    except:
        traceback.print_exc()

fig = plt.figure()

bounds = sierpinski.get_laser_coordinate_bounds()
axs = [fig.add_subplot(1, NUM_LASERS, i + 1) for i in range(NUM_LASERS)]
collections = []
for i, ax in enumerate(axs):
    ax.set_xlim([0, 4095])
    ax.set_ylim([0, 4095])
    ax.set_aspect('equal')
    ax.set_title(f'Laser {i + 1}')
    segs, colors = get_segment_data(segments[i])
    coll = mc.LineCollection(segs, colors=colors)
    collections.append(coll)
    ax.add_collection(coll)
    for i in range(len(bounds)):
        ax.plot([bounds[i][0], bounds[(i + 1) % len(bounds)][0]], 
                [bounds[i][1], bounds[(i + 1) % len(bounds)][1]],
                c='k', alpha=0.3)

for i in range(NUM_LASERS):
    threading.Thread(target=_laser_thread, args=(i,), daemon=True).start()

def animate(_):
    for i in range(NUM_LASERS):
        segs, colors = get_segment_data(segments[i])
        collections[i].set_segments(segs)
        collections[i].set_colors(colors)

if __name__ == '__main__':
    ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
    plt.show()
