"""Module providing laser update and display functionality"""
import os
from typing import List
from matplotlib import collections as mc
import sacn

class Laser:
    """Class representing a laser"""
    def __init__(self, ax, pos: int):
        cid = [0] * 16
        cid[0] = 1
        cid[-1] = pos
        self.pos = pos
        self.sacn_sender = sacn.sACNsender(source_name="Laser Controller", cid=tuple(cid))
        self.sacn_sender.manual_flush = True
        self.sacn_sender.activate_output(1)
        #target_ip = f"192.168.11.{11 + pos}"
        self.sacn_sender[1].destination = "127.0.0.1" #target_ip if self._ping(target_ip) else "127.0.0.1"
        self.sacn_enabled = True
        self.ax = ax
        self.segments = []
        self.colors = []

    def _ping(self, address) -> bool:
        """Returns True if address is pingable"""
        return not os.system(f'ping {address} -n 1')

    def _xy_to_sacn(self, x, y) -> List[int]:
        """Converts two 12 bit values to three 8 bit values for sACN"""
        return [x >> 4, (x & 0xf) << 4 | y >> 8, y & 0xff]

    def _divide_chunks(self, l, n) -> List[List]:
        """Splits a list into chunks of size n"""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def update_data(self, segments, colors) -> None:
        """Update the raw laser data"""
        self.segments = segments
        self.colors = colors
        if self.sacn_enabled and any(self.segments):
            sacn_outputs = []
            sacn_outputs.extend(self._xy_to_sacn(*self.segments[0][0]))
            sacn_outputs.extend([0, 0, 0])
            for s, c in zip([i[1] for i in self.segments], self.colors):
                sacn_outputs.extend(self._xy_to_sacn(*s))
                sacn_outputs.extend([c[0], c[1], c[2]])

            sacn_chunked_outputs = list(self._divide_chunks(sacn_outputs, 510))
            for i, data in enumerate(sacn_chunked_outputs):
                self.sacn_sender[1].dmx_data = tuple(data)
                self.sacn_sender.flush([1])

    def update_plot(self) -> None:
        """Get new signal data and update plot"""
        self.ax.clear()
        self.ax.add_collection(mc.LineCollection(self.segments, colors=[[c[0] / 255, c[1] / 255, c[2] / 255] for c in self.colors]))
        self.ax.set_xlim([0, 4095])
        self.ax.set_ylim([0, 4095])
        self.ax.set_aspect('equal')
