"""This module handles all the sACN ouputs"""
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

    def set_display(self, disp_num, line1, line2) -> None:
        if disp_num == 0:
            self.outputs[0:40] = list(line1.ljust(40).encode())
            self.outputs[40:80] = list(line2.ljust(40).encode())
        elif disp_num == 1:
            self.outputs[80:120] = list(line1.ljust(40).encode())
            self.outputs[120:160] = list(line2.ljust(40).encode())

    def update_output(self) -> None:
        self.sender[1].dmx_data = tuple(self.outputs)

    def start(self) -> None:
        """Starts sACN output"""
        self.sender.start()

    def stop(self) -> None:
        """Stops sACN output"""
        self.sender.stop()

if __name__ == '__main__':
    import time
    sacn = SACNHandler('127.0.0.1')
    #sacn = SACNHandler('10.0.0.20')
    sacn.start()
    sacn.set_display(0, "Hello", "World")
    sacn.set_display(1, "Test", "Second Display")
    for i in range(160, 181, 1):
        print(f'Updating {i}')
        for j in range(0, 256, 16):
            sacn.outputs[i] = j
            sacn.update_output()
            time.sleep(0.02)
        for j in range(0, 256, 16):
            sacn.outputs[i] = 255 - j
            sacn.update_output()
            time.sleep(0.02)

    sacn.stop()
