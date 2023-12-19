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
    import time
    import math

    def clamp(x, min_val, max_val):
        return max(min(max_val, x), min_val)

    def cube(x):
        return clamp((int)(x * x * x / 255 / 255), 0, 255)

    def nightrider():
        while True:
            dotIndex = math.sin(time.time() * 4) * 5 + 2.5
            yield [cube(255 - 51 * abs(i - dotIndex)) for i in range(6)]

    def pulse():
        output = [0 for _ in range(15)]
        while True:
            mouthColorIndex = math.sin(time.time() * 50 * math.pi / 180) + 1
            mouthRedLevel = cube(255 - 85 * abs(0 - mouthColorIndex))
            mouthWhiteLevel = cube(255 - 85 * abs(1 - mouthColorIndex))
            mouthBlueLevel = cube(255 - 85 * abs(2 - mouthColorIndex))
            for i in range(5):
                output[i] = int((math.sin(time.time() * 4) + 1) * 128 * mouthRedLevel / 255)
                output[i + 5] = int((math.sin(time.time() * 4) + 1) * 128 * mouthWhiteLevel / 255)
                output[i + 10] = int((math.sin(time.time() * 4) + 1) * 128 * mouthBlueLevel / 255)
            yield output


    dots_gen = nightrider()
    mouth_gen = pulse()

    sacn = SACNHandler('127.0.0.1')
    #sacn = SACNHandler('10.0.0.20')
    sacn.start()
    sacn.set_display(0, "Hello", "World")
    sacn.set_display(1, "Test", "Second Display")

    start_time = time.time()
    while time.time() - start_time < 10:
        sacn.outputs[160:175] = next(mouth_gen)
        sacn.outputs[175:181] = next(dots_gen)
        sacn.update_output()
        time.sleep(0.02)
    sacn.stop()
