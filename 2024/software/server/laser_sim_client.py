"""Flask client test"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import collections as mc
import requests
from laser_point import *

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, laser_id: int, ip_address: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title('Test Laser Client')
        self.geometry('400x400')
        self.laser_id = laser_id
        self.ip_address = ip_address
        self.prev_point = LaserPoint(self.laser_id)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._update_laser_plot()

    def _update_laser_plot(self):
        r = requests.get(f'http://{self.ip_address}/laser_data/{self.laser_id}/1024/')
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
        self.after(10, self._update_laser_plot)

if __name__ == '__main__':
    MainApp(laser_id=0, ip_address='127.0.0.1').mainloop()
    #MainApp(laser_id=0, ip_address='10.0.0.2').mainloop()
