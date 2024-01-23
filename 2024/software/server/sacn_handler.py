"""This module handles all the sACN ouputs"""
import time
import sacn

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

    def set_mouth(self, values: list[int]) -> None:
        """Sets the mouth buffers"""
        if len(values) != 15:
            raise ValueError(f'Set_mouth requires 15 values, but we received {len(values)} values')
        self.outputs[160:175] = values

    def set_dots(self, values: list[int]) -> None:
        """Sets the dot buffers"""
        if len(values) != 6:
            raise ValueError(f'Set_dots requires 6 values, but we received {len(values)} values')
        self.outputs[175:181] = values

    def set_buttons(self, values: list[int]) -> None:
        """Sets the button buffers"""
        if len(values) != 7:
            raise ValueError(f'Set_buttons requires 7 values, but we received {len(values)} values')
        self.outputs[181:184] = values

    def set_motors(self, values: list[int]) -> None:
        """Sets the motor buffers"""
        if len(values) != 3:
            raise ValueError(f'Set_motors requires 3 values, but we received {len(values)} values')
        self.outputs[185:192] = values

    def set_lamp(self, value: int) -> None:
        """Sets the lamp buffer"""
        self.outputs[184] = value

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
        self.sender.stop()

if __name__ == '__main__':
    from robbie_generators import *

    dots_gen = dots_nightrider()
    mouth_gen = mouth_pulse()

    #sacn = SACNHandler('127.0.0.1')
    sacn = SACNHandler('10.0.0.20')
    sacn.start()

    for i in range(160, 192, 1):
        sacn.outputs[i] = 255
        sacn.update_output()
        time.sleep(0.2)
        sacn.outputs[i] = 0
    sacn.update_output()

    start_time = time.time()
    while time.time() - start_time < 10:
        sacn.outputs[160:175] = next(mouth_gen)
        sacn.outputs[175:181] = next(dots_gen)
        sacn.update_output()
        time.sleep(0.02)

    sacn.outputs[:] = [0] * len(sacn.outputs)
    sacn.update_output()
    time.sleep(0.1)

    sacn.stop()
