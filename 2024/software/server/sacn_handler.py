"""This module handles all the sACN ouputs"""

import time
import threading
import pygame
import sacn
import robbie_generators

class SACNHandler:
    """This class implements sACN output functions"""

    def __init__(self, target_ip: str) -> None:
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
        self.outputs = [0 for _ in range(80 + 80 + 15 + 6 + 3 + 1 + 7)]

        self.animations = [
            (self.set_dots, robbie_generators.dots_nightrider()),
            (self.set_mouth, robbie_generators.mouth_pulse()),
            (self.set_motors, robbie_generators.motors_spin()),
            (self.set_lamp, robbie_generators.lamp_morse_code())
        ]
        self.animation_thread = threading.Thread(target=self._animation_thread, daemon=True)
        self.animation_running = False

        self.button_key_map = {
            pygame.K_UP: 190,
            pygame.K_DOWN: 187,
            pygame.K_LEFT: 186,
            pygame.K_RIGHT: 188,
            pygame.K_RETURN: 189,
            pygame.K_SPACE: 185,
            pygame.K_POWER: 191
        }

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

    def start(self) -> None:
        """Starts sACN output"""
        self.sender.start()

    def stop(self) -> None:
        """Stops sACN output"""
        if self.animation_running:
            self.stop_animations()
        self.sender.stop()

    def _animation_thread(self) -> None:
        print('Starting animation thread')
        while self.animation_running:
            for set_func, gen in self.animations:
                start_time = time.time()
                while time.time() - start_time < 10 and self.animation_running:
                    set_func(next(gen))
                    self.update_output()
                    time.sleep(0.02)
                set_func(None)
                self.update_output()
                start_time = time.time()
                while time.time() - start_time < 10 and self.animation_running:
                    pass
        print('Animation thread ended')

    def start_animations(self) -> None:
        self.animation_running = True
        if not self.animation_thread.is_alive():
            self.animation_thread.start()

    def stop_animations(self) -> None:
        self.animation_running = False
        while self.animation_thread.is_alive():
            pass


if __name__ == '__main__':
    #sacn = SACNHandler('127.0.0.1')
    sacn = SACNHandler('10.0.0.20')
    sacn.start()

    sacn.clear_display(0)
    sacn.clear_display(1)

    for i in range(160, 192, 1):
        sacn.outputs[i] = 255
        sacn.update_output()
        time.sleep(0.5)
        sacn.outputs[i] = 0
    sacn.update_output()

    sacn.outputs[:] = [0] * len(sacn.outputs)
    sacn.clear_display(0)
    sacn.clear_display(1)
    sacn.update_output()
    time.sleep(0.1)

    sacn.stop()
