"""Main entry point"""

import pygame 
import laser_server
import song_handler
import sacn_handler
import synthesizer
import wand
import utilities

UPDATE_SONGS = pygame.USEREVENT
BLE_WAND_CONNECT = pygame.USEREVENT + 1
BLE_WAND_DISCONNECT = pygame.USEREVENT + 2
REFOCUS = pygame.USEREVENT + 3
  
class MainApp:
    """Class representing the GUI"""
    def __init__(self, num_lasers: int, host_ip: str, target_ip: str) -> None:
        pygame.init()
        self.APP_NAME = 'Laser Control Station'
        self.focusing = True
        self.font = pygame.font.SysFont('Arial', 32)
        self.wands = { -1: wand.WandSimulator() }

        self.laser_server = laser_server.LaserServer(num_lasers, host_ip, self.wands)

        self.songs = song_handler.SongHandler(self.laser_server)
        self.current_letter = ord('A')
        self.current_number = 0
        self.current_mode = 0

        self.sacn = sacn_handler.SACNHandler(target_ip, self.songs)
        self.synth = synthesizer.SynthServer(self.wands)
        self.wand_server = wand.WandServer(
            connected_callback=lambda wand: pygame.event.post(pygame.event.Event(BLE_WAND_CONNECT, wand=wand)),
            disconnected_callback=lambda name: pygame.event.post(pygame.event.Event(BLE_WAND_DISCONNECT, wand_addr=name)))

        self.labels = { 'Mode': '0 - Invalid Mode',
                        'Song Input': 'A0',
                        'Playing': 'None',
                        'Song Queue': 'Empty',
                        'Wands': '1 (Simulated)',
                        'Synthesizer': 'Not Running',
                        'Focusing': 'True' }

        # Maps mode number to name and whether the jukebox music is playing
        self.modes = { 1: ('Jukebox', True), 
                       2: ('Audio Visualization', True), 
                       3: ('Equations', True), 
                       4: ('Spirograph', True), 
                       5: ('Pong', True), 
                       6: ('Drums', False), 
                       7: ('Wand Music', False), 
                       8: ('Robbie', False),
                       9: ('Calibration', False) }

    def _update_screen(self, screen: pygame.Surface) -> None:
        x = screen.get_size()[0] // 2
        screen.fill((255, 255, 255))
        for i, (name, value) in enumerate(self.labels.items()):
            text = self.font.render(f'{name}: {value}', True, (0, 0, 0))
            rect = text.get_rect()
            rect.center = (x, 15 + i * 40)
            screen.blit(text, rect)
        pygame.display.update()

    def music_allowed(self) -> bool:
        return self.current_mode in self.modes and self.modes[self.current_mode][1]
    
    def in_mode(self, mode: str) -> bool:
        return self.current_mode in self.modes and self.modes[self.current_mode][0] == mode

    def show_screen(self) -> None:
        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((750, 300), pygame.RESIZABLE)
        pygame.display.set_caption(self.APP_NAME)
        pygame.time.set_timer(UPDATE_SONGS, 100)
        pygame.time.set_timer(REFOCUS, 3000, 1)
        
        while True:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.sacn.stop()
                    self.laser_server.stop()
                    self.synth.stop_server()
                    self.wand_server.stop_udp()
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in range(48, 58):
                        self.current_mode = event.key - 48
                        self.laser_server.mode = self.current_mode
                        if self.current_mode in self.modes:
                            mode_name = f'{self.current_mode} - {self.modes[self.current_mode][0]}'
                            self.songs.set_music_playing(self.music_allowed())
                            self.sacn.enable_robbie_sounds = self.in_mode('Robbie')
                        else:
                            mode_name = 'Invalid Mode'
                        self.labels['Mode'] = mode_name
                        for k, w in self.wands.items():
                            w.impact_callback = self.songs.play_effect if self.in_mode('Drums') else None
                            if self.in_mode('Wand Music'):
                                self.synth.start_synth(k)
                            else:
                                self.synth.stop_all_synths()
                    elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        self._update_selection(event.key)
                        if self.in_mode('Robbie'):
                            self.sacn.force_animation(event.key)
                    elif event.key == pygame.K_RETURN:
                        if self.music_allowed():
                            self.songs.add_to_queue(self.current_letter, self.current_number)
                    elif event.key == pygame.K_SPACE:
                        if self.music_allowed():
                            self.songs.play_next_song()
                    elif event.key == pygame.K_f:
                        self.focusing = not self.focusing
                        self.labels['Focusing'] = self.focusing
                    elif event.key == pygame.K_m and -1 in self.wands:
                        self.wands[-1].press_button(True)
                    self._update_screen(screen)
                    self.sacn.key_down(event.key)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_m and -1 in self.wands:
                        self.wands[-1].press_button(False)
                elif event.type == UPDATE_SONGS:
                    if self.music_allowed():
                        self.songs.update()
                    song_queue = ' '.join([x.song_id_str for x in self.songs.song_queue])
                    if len(song_queue) > 28:
                        song_queue = f'{song_queue[:25]}...'
                    self.labels['Playing'] = self.songs.current_song.running_str if self.songs.current_song else 'None'
                    self.labels['Song Queue'] = song_queue if song_queue else 'Empty'
                    self.labels['Synthesizer'] = 'Running' if self.synth.running else 'Not Running'
                    self._update_lcds()
                    self._update_screen(screen)
                elif event.type == BLE_WAND_CONNECT:
                    if -1 in self.wands:
                        del self.wands[-1]
                    self.wands[event.wand.address] = event.wand
                    self.labels['Wands'] = f'{len(self.wands)}'
                elif event.type == BLE_WAND_DISCONNECT:
                    if event.wand_addr in self.wands:
                        del self.wands[event.wand_addr]
                        self.labels['Wands'] = f'{len(self.wands)}'
                        if len(self.wands) == 0:
                            self.wands[-1] = wand.WandSimulator()
                            self.labels['Wands'] = '1 (Simulated)'
                elif event.type == REFOCUS or (event.type == pygame.ACTIVEEVENT and event.state & 2 == 2 and not event.gain):
                    if self.focusing:
                        utilities.focus(self.APP_NAME)
                                            
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
    if utilities.ping('10.0.0.2'):
        app = MainApp(num_lasers=3, host_ip='10.0.0.2', target_ip='10.0.0.20')
    else:
        app = MainApp(num_lasers=3, host_ip='127.0.0.1', target_ip='127.0.0.1')
    app.laser_server.start()
    app.synth.start_server()
    app.wand_server.start_udp()
    app.sacn.start()
    app.show_screen()
