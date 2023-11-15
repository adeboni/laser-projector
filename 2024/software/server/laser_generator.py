"""This module generates data for the lasers"""
import time
from threading import Thread
from typing import Tuple, Callable
import numpy as np

class LaserGenerator:
    """This class generates data for the lasers"""
    def __init__(self, num_lasers: int, callback: Callable):
        self.mode = 0
        self.num_lasers = num_lasers
        self.gen = Thread(target=self._signal_source)
        self.callback = callback
        self.running = False
        self.mode_list = {0: self._circle, 1: self._rainbow_circle}

    def start(self) -> None:
        """Starts the generator"""
        if self.gen.is_alive():
            return
        self.running = True
        self.gen.start()

    def stop(self) -> None:
        """Stops the generator"""
        self.running = False
        self.gen.join()

    def _circle(self) -> dict[int, Tuple[list, list]]:
        """Generates a red circle"""
        t = time.time() * 100
        phi = np.linspace(0, 360, 90) * np.pi / 180
        x = (np.sin(t * np.pi / 180) * 400 + 600) * np.sin(phi) + 2048
        y = (np.sin(t * np.pi / 180) * 400 + 600) * np.cos(phi) + 2048
        segments = [[(int(x1), int(y1)), (int(x2), int(y2))] for x1, x2, y1, y2 in zip(x, x[1:], y, y[1:])]
        colors = [[255, 0, 0] for _ in segments]
        return [(segments, colors) for _ in range(self.num_lasers)]

    def _rainbow_circle(self) -> dict[int, Tuple[list, list]]:
        """Generates a rainbow circle"""
        t = time.time() * 100
        phi = np.linspace(0, 360, 90) * np.pi / 180
        x = (np.sin(t * np.pi / 180) * 400 + 600) * np.sin(phi) + 2048
        y = (np.sin(t * np.pi / 180) * 400 + 600) * np.cos(phi) + 2048
        colors = (np.stack((np.cos(phi), np.cos(phi + 2 * np.pi / 3), np.cos(phi - 2 * np.pi / 3))).T + 1) * 127.5
        colors = [[int(c[0]), int(c[1]), int(c[2])] for c in colors]
        segments = [[(int(x1), int(y1)), (int(x2), int(y2))] for x1, x2, y1, y2 in zip(x, x[1:], y, y[1:])]
        return [(segments, colors) for _ in range(self.num_lasers)]

    def _signal_source(self) -> dict[int, Tuple[list, list]]:
        """Simulate a signal source"""
        while self.running:
            if self.callback is not None:
                if self.mode in self.mode_list:
                    self.callback(self.mode_list[self.mode]())
                else:
                    self.callback(None)
            time.sleep(0.033)
