"""Main entry point"""
import tkinter as tk
from laser_server import LaserServer
from song_handler import SongHandler
from sacn_handler import SACNHandler

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, num_lasers: int, host_ip: str, target_ip: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title('Laser Control Station')
        self.geometry('1000x300')

        self.songs = SongHandler()
        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        self.laser_server = LaserServer(num_lasers, host_ip)
        self.laser_server.start()

        self.sacn = SACNHandler(target_ip)
        self.sacn.start()

        self._setup_labels()
        self._setup_binding()
        self._update_song_status()

        self._update_selection(None)
        self._update_mode(None)

    def _on_closing(self) -> None:
        self.sacn.stop()
        self.destroy()

    def _setup_labels(self) -> None:
        self.mode = tk.Label(self, font=('Arial', 25))
        self.mode.pack()

        self.song_selection = tk.Label(self, font=('Arial', 25))
        self.song_selection.pack()

        self.current_song = tk.Label(self, font=('Arial', 25))
        self.current_song.pack()

        self.song_queue = tk.Label(self, font=('Arial', 25))
        self.song_queue.pack()

    def _setup_binding(self) -> None:
        for c in ['<Up>', '<Down>', '<Left>', '<Right>']:
            self.bind(c, self._update_selection)
        for i in range(8):
            self.bind(str(i), self._update_mode)
        self.bind('<Return>', lambda _e: self.songs.add_to_queue(self.current_letter, self.current_number))
        self.bind('<space>', lambda _e: self.songs.play_next_song())
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _update_selection(self, e) -> None:
        if e is not None:
            if e.keycode == 38 and chr(self.current_letter) != self.songs.get_booklet_letter_limit():
                self.current_letter += 1
            elif e.keycode == 40 and chr(self.current_letter) != 'A':
                self.current_letter -= 1
            elif e.keycode == 37 and self.current_number != 0:
                self.current_number -= 1
            elif e.keycode == 39 and self.current_number != 9:
                self.current_number += 1
        self.song_selection.config(text=f'Song Input: {chr(self.current_letter)}{self.current_number}')

    def _update_mode(self, e) -> None:
        if e is not None:
            self.current_mode = int(e.char)
            self.laser_server.mode = self.current_mode
        self.mode.config(text=f'Mode: {self.current_mode}')

    def _update_song_status(self) -> None:
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
                
if __name__ == '__main__':
    MainApp(num_lasers=3, host_ip='127.0.0.1', target_ip='127.0.0.1').mainloop()
    #MainApp(num_lasers=3, host_ip='10.0.0.2', target_ip='10.0.0.20').mainloop()
