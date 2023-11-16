"""Flask client test"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import collections as mc
import requests

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Test Laser Client')
        self.geometry('600x600')
        self.resizable(False, False)
        self.prev_point = [0, 0]
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self._update_laser_plot()

    def _divide_chunks(self, l, n) -> list:
        """Splits a list into chunks of size n"""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def _bytes_to_xy(self, b0: int, b1: int, b2: int) -> list[int]:
        """Converts three 8 bit values to two 12 bit values"""
        return [b0 << 4 | b1 >> 4, (b1 & 0x0f) << 8 | b2]

    def _update_laser_plot(self):
        r = requests.get("http://127.0.0.1:8100/laser_data/1024/")
        raw_bytes = list(r.content)
        
        segments = []
        colors = []
        for p in self._divide_chunks(raw_bytes, 6):
            if len(p) != 6:
                break
            new_point = self._bytes_to_xy(p[0], p[1], p[2])
            segments.append([self.prev_point, new_point])
            colors.append([p[3], p[4], p[5]])
            self.prev_point = new_point

        self.ax.clear()
        self.ax.add_collection(mc.LineCollection(segments, colors=colors))
        self.ax.set_xlim([0, 4095])
        self.ax.set_ylim([0, 4095])
        self.ax.set_aspect('equal')
        self.fig.canvas.draw()
        self.after(100, self._update_laser_plot)

if __name__ == '__main__':
    MainApp().mainloop()
