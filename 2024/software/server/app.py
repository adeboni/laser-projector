"""Main entry point"""
import pygame 
from laser_server import LaserServer
from song_handler import SongHandler
from sacn_handler import SACNHandler
  
class MainApp:
    """Class representing the GUI"""
    def __init__(self, num_lasers: int, host_ip: str, target_ip: str) -> None:
        pygame.init()
        self.font = pygame.font.SysFont('Arial', 32)
        self.labels = {'Mode': '0',
                       'Song Input': 'A0',
                       'Current Song': 'None',
                       'Song Queue': 'Empty'}

        self.songs = SongHandler()
        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        self.laser_server = LaserServer(num_lasers, host_ip)
        self.laser_server.start_generator()

        self.sacn = SACNHandler(target_ip)
        self.sacn.start()

    def show_screen(self) -> None:
        screen = pygame.display.set_mode((750, 300), pygame.RESIZABLE)
        pygame.display.set_caption('Laser Control Station')
        update_songs = pygame.USEREVENT
        pygame.time.set_timer(update_songs, 100) 

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sacn.stop()
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in range(48, 58):
                        self.current_mode = event.key - 48
                        self.laser_server.mode = self.current_mode
                        self.labels['Mode'] = f'{self.current_mode}'
                    elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        self._update_selection(event.key)
                    elif event.key == pygame.K_RETURN:
                        self.songs.add_to_queue(self.current_letter, self.current_number)
                    elif event.key == pygame.K_SPACE:
                        self.songs.play_next_song()
                elif event.type == update_songs:
                    self.songs.update()
                    song_queue = ", ".join([x.song_id_str for x in self.songs.song_queue])
                    self.labels['Current Song'] = self.songs.current_song.running_str if self.songs.current_song else 'None'
                    self.labels['Song Queue'] = song_queue if song_queue else 'Empty'

                x = screen.get_size()[0] // 2
                screen.fill((255, 255, 255))
                for i, (name, value) in enumerate(self.labels.items()):
                    text = self.font.render(f'{name}: {value}', True, (0, 0, 0))
                    rect = text.get_rect()
                    rect.center = (x, 15 + i * 40)
                    screen.blit(text, rect)
                pygame.display.update()
                
    def start_server(self) -> None:
        self.laser_server.start_server()

    def _update_selection(self, key: int) -> None:
        if key == pygame.K_UP and chr(self.current_letter) != self.songs.get_booklet_letter_limit():
            self.current_letter += 1
        elif key == pygame.K_DOWN and chr(self.current_letter) != 'A':
            self.current_letter -= 1
        elif key == pygame.K_LEFT and self.current_number != 0:
            self.current_number -= 1
        elif key == pygame.K_RIGHT and self.current_number != 9:
            self.current_number += 1
        self.labels['Song Input'] = f'{chr(self.current_letter)}{self.current_number}'
       
if __name__ == '__main__':
    app = MainApp(num_lasers=3, host_ip='127.0.0.1', target_ip='127.0.0.1')
    # app = MainApp(num_lasers=3, host_ip='10.0.0.2', target_ip='10.0.0.20')
    app.start_server()
    app.show_screen()
