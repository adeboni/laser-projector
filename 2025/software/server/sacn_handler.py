"""This module handles all the sACN ouputs"""

import random
import time
import threading
import sacn
import robbie_generators

class SACNHandler:
    """This class implements sACN output functions"""

    def __init__(self, target_ip: str, song_handler) -> None:
        self.song_handler = song_handler
        self.enable_robbie_sounds = False

        self.sender = sacn.sACNsender()
        self.sender.activate_output(1)
        self.sender[1].destination = target_ip

        """
        Outputs:
        0-79 = Display 1
        80-159 = Display 2
        160-174 = Mouth
        175-180 = Dots
        181-183 = Motors
        184 = Lamp
        185-191 = Buttons
        """
        self.outputs = [0] * (80 + 80 + 15 + 6 + 3 + 1 + 7)

        self.animations = [
            (self.set_dots, robbie_generators.dots_nightrider()),
            (self.set_mouth, robbie_generators.mouth_pulse()),
            (self.set_motors, robbie_generators.motors_spin()),
            (self.set_lamp, robbie_generators.lamp_morse_code())
        ]
        self.animation_thread = threading.Thread(target=self._animation_thread, daemon=True)
        self.animation_running = False
        self._animation_event = threading.Event()

        self.button_key_map = {
            1073741906: 190, # UP
            1073741905: 187, # DOWN
            1073741904: 186, # LEFT
            1073741903: 188, # RIGHT
            13: 189,         # RETURN
            32: 185,         # SPACE
            1073741926: 191  # POWER
        }

        self.animation_key_map = {
            1073741906: 0, # UP
            1073741905: 1, # DOWN
            1073741904: 2, # LEFT
            1073741903: 3, # RIGHT
        }

    def force_animation(self, key: int) -> None:
        if key in self.animation_key_map:
            ani_thread = threading.Thread(target=self._manual_animation_thread, args=(self.animation_key_map[key],), daemon=True)
            ani_thread.start()

    def _manual_animation_thread(self, id: int) -> None:
        set_func, gen = self.animations[id]
        start_time = time.time()
        while time.time() - start_time < 10:
            set_func(next(gen))
            self.update_output()
            time.sleep(0.02)
        set_func(None)
        self.update_output()

    def _key_thread(self, output_num: int) -> None:
        self.outputs[output_num] = 255
        self.update_output()
        time.sleep(0.4)
        self.outputs[output_num] = 0
        self.update_output()

    def key_down(self, key: int) -> None:
        if key in self.button_key_map:
            key_thread = threading.Thread(target=self._key_thread, args=(self.button_key_map[key],), daemon=True)
            key_thread.start()

    def set_mouth(self, values: list[int] | None) -> None:
        """Sets the mouth buffers"""
        if values and len(values) != 15:
            raise ValueError(f'Set_mouth requires 15 values, but we received {len(values)} values')
        self.outputs[160:175] = values if values else [0] * 15

    def set_dots(self, values: list[int] | None) -> None:
        """Sets the dot buffers"""
        if values and len(values) != 6:
            raise ValueError(f'Set_dots requires 6 values, but we received {len(values)} values')
        self.outputs[175:181] = values if values else [0] * 6

    def set_buttons(self, values: list[int] | None) -> None:
        """Sets the button buffers"""
        if values and len(values) != 7:
            raise ValueError(f'Set_buttons requires 7 values, but we received {len(values)} values')
        self.outputs[185:192] = values if values else [0] * 7

    def set_motors(self, values: list[int] | None) -> None:
        """Sets the motor buffers"""
        if values and len(values) != 3:
            raise ValueError(f'Set_motors requires 3 values, but we received {len(values)} values')
        self.outputs[181:184] = values if values else [0] * 3

    def set_lamp(self, value: int | None) -> None:
        """Sets the lamp buffer"""
        self.outputs[184] = value if value else 0

    def clear_display(self, disp_num: int) -> None:
        self.set_display(disp_num, " ", " ")

    def set_display(self, disp_num: int, line1: str, line2: str) -> None:
        """Updates the display buffers"""
        if disp_num == 0:
            self.outputs[0:40] = list(line1.ljust(40).encode())
            self.outputs[40:80] = list(line2.ljust(40).encode())
        elif disp_num == 1:
            self.outputs[80:120] = list(line1.ljust(40).encode())
            self.outputs[120:160] = list(line2.ljust(40).encode())

    def update_output(self) -> None:
        """Sends the pending buffer out to the network"""
        self.sender[1].dmx_data = tuple(self.outputs)

    def start(self, animations: bool=True) -> None:
        """Starts sACN output"""
        self.sender.start()
        if animations and not self.animation_running:
            print('Starting animation thread')
            self.animation_running = True
            self.animation_thread.start()

    def stop(self) -> None:
        """Stops sACN output"""
        if self.animation_running:
            print('Stopping animation thread')
            self.animation_running = False
            self._animation_event.set()
            self.animation_thread.join()
        self.sender.stop()

    def _animation_thread(self) -> None:
        sound_idx = None
        while self.animation_running:
            selected_animations = random.sample(self.animations, random.randrange(1, len(self.animations)))
            if self.enable_robbie_sounds:
                if sound_idx is None or not self.song_handler.robbie_sounds[sound_idx].is_playing():
                    sound_idx = self.song_handler.play_robbie_sound()
            start_time = time.time()
            while time.time() - start_time < 30 and self.animation_running:
                for set_func, gen in selected_animations:
                    set_func(next(gen))
                self.update_output()
                time.sleep(0.02)
            for set_func, gen in selected_animations:
                set_func(None)
            self.update_output()
            self._animation_event.wait(30)

if __name__ == '__main__':
    sacn = SACNHandler('127.0.0.1')
    #sacn = SACNHandler('10.0.0.20')
    sacn.start(animations=False)

    sacn.clear_display(0)
    sacn.clear_display(1)

    try:
        for i in range(160, 192, 1):
            sacn.outputs[i] = 255
            sacn.update_output()
            time.sleep(0.5)
            sacn.outputs[i] = 0
        sacn.update_output()
    except KeyboardInterrupt:
        pass

    sacn.outputs[:] = [0] * len(sacn.outputs)
    sacn.clear_display(0)
    sacn.clear_display(1)
    sacn.update_output()
    time.sleep(0.1)
    sacn.stop()
