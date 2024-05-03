"""Main entry point"""

import pygame 
import decorators
import laser_server
import song_handler
import sacn_handler
import synthesizer
import wand
  
class MainApp:
    """Class representing the GUI"""
    def __init__(self, num_lasers: int, host_ip: str, target_ip: str) -> None:
        pygame.init()
        self.laser_server = laser_server.LaserServer(num_lasers, host_ip)
        self.sacn = sacn_handler.SACNHandler(target_ip)
        self.synth = synthesizer.SynthServer()
        self.wand_scanner = wand.BLEScanner()

        self.font = pygame.font.SysFont('Arial', 32)
        self.wands = { -1: wand.WandSimulator() }
        self.laser_server.set_wands(self.wands)
        self.labels = { 'Mode': '0 - Invalid Mode',
                        'Song Input': 'A0',
                        'Playing': 'None',
                        'Song Queue': 'Empty',
                        'Wands': '1 (Simulated)',
                        'Synthesizer': 'Not Running' }

        self.songs = song_handler.SongHandler(self.laser_server)
        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        # Maps mode number to name and whether the jukebox music is playing
        self.modes = { 1: ('Jukebox', True), 
                       2: ('Audio Visualization', True), 
                       3: ('Equations', True), 
                       4: ('Spirograph', True), 
                       5: ('Pong', True), 
                       6: ('Wand Drawing', True), 
                       7: ('Wand Music', False), 
                       8: ('Drums', False),
                       9: ('Calibration', False) }

    @decorators.threaded_time_delay(5)
    def start_sacn(self):
        self.sacn.start()
        self.sacn.start_animations()

    def _update_screen(self, screen: pygame.Surface) -> None:
        x = screen.get_size()[0] // 2
        screen.fill((255, 255, 255))
        for i, (name, value) in enumerate(self.labels.items()):
            text = self.font.render(f'{name}: {value}', True, (0, 0, 0))
            rect = text.get_rect()
            rect.center = (x, 15 + i * 40)
            screen.blit(text, rect)
        pygame.display.update()

    def show_screen(self) -> None:
        screen = pygame.display.set_mode((750, 300), pygame.RESIZABLE)
        pygame.display.set_caption('Laser Control Station')
        UPDATE_SONGS = pygame.USEREVENT
        pygame.time.set_timer(UPDATE_SONGS, 100)
        clock = pygame.time.Clock()

        while True:
            clock.tick(50)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    decorators.is_closing = True
                    self.sacn.stop()
                    self.laser_server.stop()
                    self.synth.stop_server()
                    self.wand_scanner.stop()
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in range(48, 58):
                        self.current_mode = event.key - 48
                        self.laser_server.mode = self.current_mode
                        if self.current_mode in self.modes:
                            mode_name = f'{self.current_mode} - {self.modes[self.current_mode][0]}'
                            self.songs.set_music_playing(self.modes[self.current_mode][1])
                        else:
                            mode_name = 'Invalid Mode'
                        self.labels['Mode'] = mode_name
                        for k, w in self.wands.items():
                            w.callback = self.songs.play_effect if self.current_mode == 8 else None
                            if self.current_mode == 7:
                                self.synth.start_synth(k)
                            else:
                                self.synth.stop_all_synths()
                    elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        self._update_selection(event.key)
                    elif event.key == pygame.K_RETURN:
                        if self.current_mode in self.modes and self.modes[self.current_mode][1]:
                            self.songs.add_to_queue(self.current_letter, self.current_number)
                    elif event.key == pygame.K_SPACE:
                        if self.current_mode in self.modes and self.modes[self.current_mode][1]:
                            self.songs.play_next_song()
                    self._update_screen(screen)
                    self.sacn.key_down(event.key)
                elif event.type == UPDATE_SONGS:
                    if self.current_mode in self.modes and self.modes[self.current_mode][1]:
                        self.songs.update()
                    song_queue = ' '.join([x.song_id_str for x in self.songs.song_queue])
                    if len(song_queue) > 28:
                        song_queue = f'{song_queue[:25]}...'
                    self.labels['Playing'] = self.songs.current_song.running_str if self.songs.current_song else 'None'
                    self.labels['Song Queue'] = song_queue if song_queue else 'Empty'
                    self.labels['Synthesizer'] = 'Running' if self.synth.running else 'Not Running'
                    self._update_lcds()
                    self._update_screen(screen)
                elif event.type == wand.BLE_WAND_CONNECT:
                    if -1 in self.wands:
                        del self.wands[-1]
                    self.wands[event.wand.name] = event.wand
                    self.labels['Wands'] = f'{len(self.wands)}'
                elif event.type == wand.BLE_WAND_DISCONNECT:
                    if event.wand_name in self.wands:
                        del self.wands[event.wand_name]
                        self.labels['Wands'] = f'{len(self.wands)}'
                        if len(self.wands) == 0:
                            self.wands[-1] = wand.WandSimulator()
                            self.labels['Wands'] = '1 (Simulated)'
                            
            for k, w in self.wands.items():
                w.update_position()
                if sp := w.get_synth_point():
                    self.synth.update_synth(k, x=sp[0], y=sp[1], r=sp[2])
                
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
        row1 = f'Playing: {self.labels["Playing"]}'
        row2 = f'Queue: {self.labels["Song Queue"]}'
        row3 = f'Mode: {self.labels["Mode"]}'
        row4 = f'Song Selection: {self.labels["Song Input"]}'
        self.sacn.set_display(0, row1, row2)
        self.sacn.set_display(1, row3, row4)
        self.sacn.update_output()
       
if __name__ == '__main__':
    import utilities
    if utilities.ping('10.0.0.2'):
        app = MainApp(num_lasers=3, host_ip='10.0.0.2', target_ip='10.0.0.20')
    else:
        app = MainApp(num_lasers=3, host_ip='127.0.0.1', target_ip='127.0.0.1')
    app.laser_server.start()
    app.synth.start_server()
    app.wand_scanner.start()
    app.start_sacn()
    app.show_screen()
