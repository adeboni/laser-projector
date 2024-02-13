from threading import Thread
import requests
import time
import traceback
from matplotlib import pyplot as plt
from matplotlib import collections as mc
from matplotlib import animation
from laser_point import *

NUM_LASERS = 3
NUM_POINTS = 1000

segments = [[LaserSegment(i)] for i in range(NUM_LASERS)]

def _laser_thread(laser_index):
    try:
        while True:
            r = requests.get(f'http://127.0.0.1:8080/laser_data/{laser_index}/2048/')
            raw_bytes = list(r.content)
            for i in range(0, len(raw_bytes), 6):
                chunk = raw_bytes[i:i + 6]
                if len(chunk) != 6:
                    break
                new_point = LaserPoint.from_bytes(laser_index, chunk)
                segments[laser_index].append(LaserSegment(laser_index, segments[laser_index][-1].end, new_point, 
                                                          [new_point.r / 255, new_point.g / 255, new_point.b / 255]))
                while len(segments[laser_index]) > NUM_POINTS:
                    segments[laser_index].pop(0)
                
            time.sleep(0.1)
    except:
        traceback.print_exc()

fig = plt.figure()
axs = [fig.add_subplot(100 + 10 * NUM_LASERS + i + 1) for i in range(NUM_LASERS)]
collections = []
for i, ax in enumerate(axs):
    ax.set_xlim([0, 4095])
    ax.set_ylim([0, 4095])
    ax.set_aspect('equal')
    #ax.set_facecolor('black')
    ax.set_title(f'Laser {i + 1}')
    segs, colors = get_segment_data(segments[i])
    coll = mc.LineCollection(segs, colors=colors)
    collections.append(coll)
    ax.add_collection(coll)

for i in range(NUM_LASERS):
    Thread(target=_laser_thread, args=(i,), daemon=True).start()

def animate(_):
    for i in range(NUM_LASERS):
        segs, colors = get_segment_data(segments[i])
        collections[i].set_segments(segs)
        collections[i].set_colors(colors)

ani = animation.FuncAnimation(fig, animate, interval=25, cache_frame_data=False)
plt.show()
