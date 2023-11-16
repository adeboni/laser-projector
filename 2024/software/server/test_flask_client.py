"""Flask client test"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import collections as mc
import requests
from laser_point import *

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, laser_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Test Laser Client')
        self.geometry('600x600')
        self.resizable(False, False)
        self.laser_id = laser_id
        self.prev_point = LaserPoint(self.laser_id)
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self._update_laser_plot()

    def _update_laser_plot(self):
        r = requests.get(f'http://127.0.0.1:8100/laser_data/{self.laser_id}/1024/')
        raw_bytes = list(r.content)
        
        segments = []
        colors = []
        for i in range(0, len(raw_bytes), 6):
            chunk = raw_bytes[i:i + 6]
            if len(chunk) != 6:
                break
            new_point = LaserPoint.from_bytes(self.laser_id, chunk)
            segments.append([[self.prev_point.x, self.prev_point.y], [new_point.x, new_point.y]])
            colors.append([new_point.r / 255, new_point.g / 255, new_point.b / 255])
            self.prev_point = new_point

        self.ax.clear()
        self.ax.add_collection(mc.LineCollection(segments, colors=colors))
        self.ax.set_xlim([0, 4095])
        self.ax.set_ylim([0, 4095])
        self.ax.set_aspect('equal')
        self.ax.set_title(f'Laser {self.laser_id + 1}')
        self.fig.canvas.draw()
        self.after(100, self._update_laser_plot)

if __name__ == '__main__':
    MainApp(laser_id=0).mainloop()
