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
        self.joysticks = {}
        self.labels = {'Mode': '0 - Invalid Mode',
                       'Song Input': 'A0',
                       'Playing': 'None',
                       'Song Queue': 'Empty',
                       'Joysticks': 'None'}

        self.songs = SongHandler()
        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        self.mode_names = {1: 'Jukebox', 
                           2: 'Wand', 
                           3: 'Pong', 
                           4: 'Mode 4', 
                           5: 'Mode 5', 
                           6: 'Mode 6', 
                           7: 'Mode 7', 
                           8: 'Mode 8'}

        self.laser_server = LaserServer(num_lasers, host_ip)
        self.laser_server.start_generator()

        self.sacn = SACNHandler(target_ip)
        self.sacn.start()
        self.sacn.start_animations()

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
                        mode_name = f'{self.current_mode} - {self.mode_names[self.current_mode] if self.current_mode in self.mode_names else "Invalid Mode"}'
                        self.labels['Mode'] = mode_name
                    elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        self._update_selection(event.key)
                    elif event.key == pygame.K_RETURN:
                        self.songs.add_to_queue(self.current_letter, self.current_number)
                    elif event.key == pygame.K_SPACE:
                        self.songs.play_next_song()
                elif event.type == update_songs:
                    self.songs.update()
                    song_queue = " ".join([x.song_id_str for x in self.songs.song_queue])
                    if len(song_queue) > 28:
                        song_queue = f'{song_queue[:25]}...'
                    self.labels['Playing'] = self.songs.current_song.running_str if self.songs.current_song else 'None'
                    self.labels['Song Queue'] = song_queue if song_queue else 'Empty'
                    self._update_lcds()
                elif event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    self.joysticks[joystick.get_instance_id()] = joystick
                    self.labels['Joysticks'] = ', '.join([x.get_name() for x in self.joysticks.items()])
                elif event.type == pygame.JOYDEVICEREMOVED:
                    self.joysticks[event.instance_id].quit()
                    del self.joysticks[event.instance_id]
                    self.labels['Joysticks'] = ', '.join([x.get_name() for x in self.joysticks.items()])

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

    def _update_lcds(self) -> None:
        row1 = f'Mode: {self.labels["Mode"]}'
        row2 = f'Song Selection: {self.labels["Song Input"]}'
        row3 = f'Playing: {self.labels["Playing"]}'
        row4 = f'Queue: {self.labels["Song Queue"]}'
        self.sacn.set_display(0, row1, row2)
        self.sacn.set_display(1, row3, row4)
        self.sacn.update_output()
       
if __name__ == '__main__':
    #app = MainApp(num_lasers=3, host_ip='127.0.0.1', target_ip='127.0.0.1')
    app = MainApp(num_lasers=3, host_ip='10.0.0.2', target_ip='10.0.0.20')
    app.start_server()
    app.show_screen()
