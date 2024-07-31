import psutil
import time
import os

while True:
    if not psutil.sensors_battery().power_plugged:
        os.system('shutdown -s -t 0')
    time.sleep(1)
