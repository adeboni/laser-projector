"""Module providing song handling functionality"""
import os
import soundfile
import laser_server
import pygame

class Song:
    """Class implementing a song"""
    def __init__(self, path: str, index: int) -> None:
        self.path = path
        self.index = index
        self.played_length_s = 0
        self.length_s = 0
        self.data = None
        self.sr = None
        self.author, self.title, self.year = os.path.splitext(os.path.basename(path))[0].split(' - ')

    @property
    def song_id(self) -> tuple[int, int]:
        """Returns the song ID as a tuple"""
        return (ord('A') + self.index // 10, self.index % 10)

    @property
    def song_id_str(self) -> str:
        """Returns the song ID as a string"""
        letter, number = self.song_id
        return f'{chr(letter)}{number}'

    @property
    def running_str(self) -> str:
        """Returns a display string with the current time"""
        pm, ps = divmod(self.played_length_s, 60)
        tm, ts = divmod(self.length_s, 60)
        time_str = f'{pm:02d}:{ps:02d}/{tm:02d}:{ts:02d}'
        title_str = self.title
        # Shorten the title string to 12 chars to fit a 40 char display
        # Playing: ID - <Title> - MM:SS/MM:SS
        if len(title_str) > 12:
            title_str = f'{title_str[:9]}...'
        return f'{self.song_id_str} - {title_str} - {time_str}'

    def __str__(self):
        return f'{self.song_id_str} - {self.author} - {self.title}'

    def play(self) -> None:
        """Plays the song"""
        self.data, self.sr = soundfile.read(self.path)
        self.length_s = int(len(self.data) / self.sr)
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.play()

    def stop(self) -> None:
        """Stops the current song"""
        pygame.mixer.music.stop()

    def update_time(self) -> None:
        """Updates the played time variable"""
        self.played_length_s = pygame.mixer.music.get_pos() // 1000

    def get_data(self, blocksize: int) -> list[float]:
        """Returns a block of data from the current audio"""
        if self.data is not None:
            start_index = int(pygame.mixer.music.get_pos() / 1000 * self.sr)
            return [x[0] for x in self.data[start_index:start_index + blocksize]]
        else:
            return None


class SongHandler:
    """Class implementing a song handler"""
    def __init__(self, laser_server: laser_server.LaserServer):
        pygame.mixer.init()
        if not os.path.exists('songs'):
            os.mkdir('songs')
        self.songs = [Song(os.path.join('songs', file), i) for i, file in enumerate(os.listdir('songs'))]
        self.song_queue = []
        self.current_song = None
        self.laser_server = laser_server

    def play_next_song(self) -> None:
        """Plays the next song in the queue"""
        if self.current_song is not None:
            self.current_song.stop()

        if any(self.song_queue):
            self.current_song = self.song_queue.pop(0)
            self.current_song.play()
            self.laser_server.set_audio_callback(self.current_song.get_data)
        else:
            self.current_song = None
            self.laser_server.set_audio_callback(None)

    def add_to_queue(self, song_letter: str, song_number: int) -> None:
        """Adds a song to the queue"""
        next_song_index = (song_letter - ord('A')) * 10 + song_number
        if next_song_index >= len(self.songs):
            return
        if any(self.song_queue) and self.song_queue[-1] == self.songs[next_song_index]:
            return
        self.song_queue.append(self.songs[next_song_index])

    def get_booklet_letter_limit(self) -> str:
        """Returns the maximum booklet letter"""
        return chr(ord('A') + (len(self.songs) - 1) // 10)

    def update(self) -> None:
        """Updates the current song timestamp and plays the next song if it finishes"""
        if self.current_song is not None:
            self.current_song.update_time()
            if self.current_song.played_length_s < 0:
                self.current_song = None

        if self.current_song is None and any(self.song_queue):
            self.play_next_song()
