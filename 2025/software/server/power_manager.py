import psutil
import time
import os

time.sleep(60)

while True:
    if not psutil.sensors_battery().power_plugged:
        time.sleep(5)
        if not psutil.sensors_battery().power_plugged:
            os.system('shutdown -s -t 0')
    time.sleep(1)
