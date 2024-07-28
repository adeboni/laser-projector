"""Module providing song handling functionality"""

import os
import random
import time
import soundfile
import laser_server
import pygame
import pathlib
import datetime

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

    def get_data(self, blocksize: int, interval: int) -> list[float]:
        """Returns a block of data from the current audio"""
        if self.data is not None:
            start_index = int(pygame.mixer.music.get_pos() / 1000 * self.sr)
            return [x[0] for x in self.data[start_index:start_index + blocksize]][::interval]
        else:
            return None
            
    def get_amplitude(self, blocksize: int, interval: int) -> float:
        """Returns the average amplitude of a block of data"""
        if raw_data := self.get_data(blocksize, interval):
            return sum([abs(x) for x in raw_data]) / len(raw_data)
        else:
            return 0
        
    def get_envelope(self, blocksize: int, interval: int, decay: float) -> list[float]:
        """Returns an envelope-followed representation of the data block"""
        raw_data = self.get_data(blocksize, interval)
        if raw_data is not None:
            result = []
            curr_value = 0
            for x in raw_data:
                result.append(curr_value := x if x > curr_value else max(x, curr_value - decay))
            return result
        else:
            return None
            
    def center_on_peak(self, data: list[float], search_area: int) -> list[float]:
        try:
            max_reading = 0
            old_center = len(data) // 2
            new_center = old_center
            for i in range(old_center - search_area, old_center + search_area):
                if data[i] > max_reading:
                    max_reading = data[i]
                    new_center = i
            new_data = [0] * len(data)
            if new_center > old_center:
                centered_data = data[new_center-old_center:]
            else:
                centered_data = data[:len(data)-(old_center-new_center)]
            start_index = (len(data) - len(centered_data)) // 2
            new_data[start_index:start_index+len(centered_data)] = centered_data
            return new_data
        except:
            return data

class Effect:
    def __init__(self, path: str) -> None:
        self.path = path
        self.name = pathlib.Path(path).stem
        self.data, self.sr = soundfile.read(self.path)
        self.length_s = len(self.data) / self.sr
        self.sound_obj = pygame.mixer.Sound(self.path)
        self.start_time = 0

    def __repr__(self) -> str:
        return f'Effect(Name: {self.name}, Length: {self.length_s})'

    def play(self) -> None:
        """Plays the file"""
        self.start_time = time.time()
        self.sound_obj.play()

    def stop(self) -> None:
        """Stops the file"""
        self.sound_obj.stop()

    def is_playing(self) -> bool:
        """Returns True if the audio is still playing"""
        return time.time() < self.start_time + self.length_s

    def get_data(self, blocksize: int, interval: int) -> list[float]:
        """Returns a block of data from the current audio"""
        if self.data is not None and self.is_playing():
            start_index = int((time.time() - self.start_time) * self.sr)
            return [x[0] for x in self.data[start_index:start_index + blocksize]][::interval]
        else:
            return None
            
    def get_amplitude(self, blocksize: int, interval: int) -> float:
        """Returns the average amplitude of a block of data"""
        if raw_data := self.get_data(blocksize, interval):
            return sum([abs(x) for x in raw_data]) / len(raw_data)
        else:
            return 0

class SongHandler:
    """Class implementing a song handler"""
    def __init__(self, laser_server: laser_server.LaserServer=None):
        pygame.mixer.init()

        if not os.path.exists('songs'):
            os.mkdir('songs')
        self.songs = [Song(os.path.join('songs', file), i) for i, file in enumerate(sorted(os.listdir('songs')))]
        self.song_queue = []
        self.current_song = None
        print(f'Found {len(self.songs)} songs')

        if not os.path.exists('effects'):
            os.mkdir('effects')
        self.effects = [Effect(os.path.join('effects', file)) for file in os.listdir('effects')]
        self.last_effect_time = 0
        print(f'Found {len(self.effects)} effect sounds')

        if not os.path.exists('robbie_sounds'):
            os.mkdir('robbie_sounds')
        self.robbie_sounds = [Effect(os.path.join('robbie_sounds', file)) for file in os.listdir('robbie_sounds')]
        print(f'Found {len(self.robbie_sounds)} Robbie sounds')

        self.pong_sounds = {
            'Wall': 'pong_sounds/wall.mp3',
            'Paddle': 'pong_sounds/paddle.mp3',
            'Game Over': 'pong_sounds/game_over.mp3'
        }
        for sound in self.pong_sounds:
            self.pong_sounds[sound] = Effect(self.pong_sounds[sound]) if os.path.exists(self.pong_sounds[sound]) else None

        self.laser_server = laser_server
        if self.laser_server:
            self.laser_server.set_song_handler(self)

    def play_next_song(self) -> None:
        """Plays the next song in the queue"""
        if self.current_song is not None:
            self.current_song.stop()

        if any(self.song_queue):
            self.current_song = self.song_queue.pop(0)
            self.current_song.play()
            with open('song_log.txt', 'a') as f:
                f.write(f'{datetime.datetime.now()}: Started {self.current_song.author} - {self.current_song.title}\r\n')
        else:
            self.current_song = None
            
        if self.laser_server:
            self.laser_server.set_song(self.current_song)

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
                with open('song_log.txt', 'a') as f:
                    f.write(f'{datetime.datetime.now()}: Finished {self.current_song.author} - {self.current_song.title}\r\n')
                self.current_song = None

        if self.current_song is None and any(self.song_queue):
            self.play_next_song()

    def set_music_playing(self, playing: bool) -> None:
        """Pauses or unpauses music"""
        if playing:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def play_effect(self, index: int=None) -> int:
        """Plays a file from the effects folder"""
        if len(self.effects) == 0:
            return
        if time.time() - self.last_effect_time < 0.3:
            return
        self.last_effect_time = time.time()
        if index is None:
            index = random.randrange(len(self.effects))
        if self.laser_server:
            self.laser_server.set_effect(self.effects[index])
        self.effects[index].play()
        return index

    def play_robbie_sound(self, index: int=None) -> int:
        """Plays a robbie sound"""
        if len(self.robbie_sounds) == 0:
            return
        if index is None:
            index = random.randrange(len(self.robbie_sounds))
        self.robbie_sounds[index].play()
        return index

    def stop_robbie_sound(self, index: int=None) -> None:
        """Stops all robbie sounds"""
        if index is None:
            for sound in self.robbie_sounds:
                sound.stop()
        else:
            self.robbie_sounds[index].stop()

    def play_pong_sound(self, key: str) -> None:
        """Plays a pong sound effect"""
        if key in self.pong_sounds and self.pong_sounds[key]:
            self.pong_sounds[key].play()
            