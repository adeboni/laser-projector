"""This module controls SuperCollider to create sounds"""

import supriya
from supriya.ugens import SinOsc, CombC, Out

@supriya.synthdef()
def simple_sine(freq=440, amplitude=0.1):
    sine = SinOsc.ar(frequency=freq) * amplitude
    Out.ar(bus=0, source=[sine, sine])

@supriya.synthdef()
def sci_fi(freq=440, x=15, amplitude=0.1):
    sine = SinOsc.ar(frequency=freq) * amplitude
    comb = CombC.ar(source=sine, maximum_delay_time=0.2, delay_time=0.13, decay_time=x)
    Out.ar(bus=0, source=[comb, comb])

class SynthServer:
    """This class handles synth server operations"""

    def __init__(self, ) -> None:
        self.server = None
        self.synths = {}

    def start_server(self) -> None:
        self.server = supriya.Server().boot()
        self.server.add_synthdefs(simple_sine)
        self.server.add_synthdefs(sci_fi)
        self.server.sync()
        
    def stop_server(self) -> None:
        for synth in list(self.synths):
            self.stop_synth(synth)
        if self.server:
            try:
                self.server.quit()
            except TimeoutError:
                pass

    def start_synth(self, id: int, synth_def) -> None:
        self.synths[id] = self.server.add_synth(synth_def)

    def stop_synth(self, id: int) -> None:
        self.synths[id].free()
        del self.synths[id]

    def update_synth(self, id: int, **kwargs) -> None:
        self.synths[id].set(**kwargs)

if __name__ == '__main__':
    import pyautogui
    import numpy as np

    screen_width, screen_height = pyautogui.size()
    server = SynthServer()
    server.start_server()
    id = 0
    server.start_synth(id, sci_fi)

    try:
        while True:
            mouse = pyautogui.position()
            freq = np.interp(mouse.y, [0, screen_width], [1200, 300])
            x = np.interp(mouse.x, [0, screen_height], [3, 15])
            server.update_synth(id, freq=freq, x=x)
    except KeyboardInterrupt:
        server.stop_server()
    