"""Main entry point"""
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import psutil
import laser
import laser_generator
import song_handler

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, num_lasers: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Laser Control Station')
        self.geometry('1200x600')
        self.resizable(False, False)
        self.songs = song_handler.SongHandler()
        self.fig = Figure(figsize=(12, 4), dpi=100)
        self.laser_gen = laser_generator.LaserGenerator(num_lasers, self._laser_gen_callback)
        self.lasers = [laser.Laser(self.fig.add_subplot(1, num_lasers, pos + 1), pos) for pos in range(num_lasers)]
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=3)

        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        self._setup_labels()
        self._setup_binding()
        self._update_power_status()
        self._update_laser_plots()
        self._update_song_status()
        self._update_selection(None)
        self._update_mode(None)

        self.laser_gen.start()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        self.laser_gen.stop()
        self.destroy()

    def _setup_labels(self):
        self.mode = tk.Label(self, font=('Arial', 25))
        self.mode.grid(row=1, column=0)

        self.power_status = tk.Label(self, font=('Arial', 25))
        self.power_status.grid(row=1, column=1)

        self.song_selection = tk.Label(self, font=('Arial', 25))
        self.song_selection.grid(row=1, column=2)

        self.current_song = tk.Label(self, font=('Arial', 25))
        self.current_song.grid(row=2, column=0, columnspan=3)

        self.song_queue = tk.Label(self, font=('Arial', 25))
        self.song_queue.grid(row=3, column=0, columnspan=3)

    def _setup_binding(self):
        for c in ['<Up>', '<Down>', '<Left>', '<Right>']:
            self.bind(c, self._update_selection)
        for i in range(8):
            self.bind(str(i), self._update_mode)
        self.bind('<Return>', lambda _e: self.songs.add_to_queue(self.current_letter, self.current_number))
        self.bind('<space>', lambda _e: self.songs.play_next_song())

    def _update_selection(self, e):
        if e is not None:
            if e.keycode == 38 and chr(self.current_letter) != self.songs.get_booklet_letter_limit():
                self.current_letter += 1
            elif e.keycode == 40 and chr(self.current_letter) != 'A':
                self.current_letter -= 1
            elif e.keycode == 37 and self.current_number != 0:
                self.current_number -= 1
            elif e.keycode == 39 and self.current_number != 9:
                self.current_number += 1
        self.song_selection.config(text = f'Song Input: {chr(self.current_letter)}{self.current_number}')

    def _update_mode(self, e):
        if e is not None:
            self.current_mode = int(e.char)
            self.laser_gen.mode = self.current_mode
        self.mode.config(text = f'Mode: {self.current_mode}')

    def _update_laser_plots(self):
        for l in self.lasers:
            l.update_plot()
        self.fig.canvas.draw()
        self.after(30, self._update_laser_plots)

    def _update_song_status(self):
        self.songs.update()

        if self.songs.current_song is None:
            self.current_song.config(text='Current Song: None')
        else:
            self.current_song.config(text=f'Current Song: {self.songs.current_song.running_str}')

        if any(self.songs.song_queue):
            self.song_queue.config(text=f'Song Queue: {", ".join([x.song_id_str for x in self.songs.song_queue])}')
        else:
            self.song_queue.config(text='Song Queue: Empty')

        self.after(100, self._update_song_status)

    def _update_power_status(self):
        self.plugged_in = psutil.sensors_battery().power_plugged
        self.power_status.config(text=f'Power Status: {"Plugged In" if self.plugged_in else "Unplugged"}')
        self.after(1000, self._update_power_status)

    def _laser_gen_callback(self, laser_data):
        if laser_data:
            for i, data in enumerate(laser_data):
                self.lasers[i].update_data(*data)
        else:
            for i in range(self.laser_gen.num_lasers):
                self.lasers[i].update_data([], [])

if __name__ == '__main__':
    MainApp(num_lasers=3).mainloop()
