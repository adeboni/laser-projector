"""This module handles all the sACN ouputs"""
import sacn

class SACNHandler:
    """This class implements sACN output functions"""

    def __init__(self) -> None:
        self.sender = sacn.sACNsender()
        self.sender.activate_output(1)
        self.sender[1].destination = "10.0.0.20"

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
    sacn = SACNHandler()
    sacn.start()
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
