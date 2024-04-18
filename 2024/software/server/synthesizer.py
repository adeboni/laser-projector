"""This module controls SuperCollider to create sounds"""

import decorators
import supriya
from supriya.ugens import SinOsc, CombC, Out

@supriya.synthdef()
def simple_sine(amplitude=0.1, x=0, y=0, r=0):
    sine = SinOsc.ar(frequency=y) * amplitude
    Out.ar(bus=0, source=[sine, sine])

@supriya.synthdef()
def sci_fi(amplitude=0.1, x=0, y=0, r=0):
    sine = SinOsc.ar(frequency=(y*800+300)) * amplitude
    comb = CombC.ar(source=sine, maximum_delay_time=0.2, delay_time=0.13, decay_time=(x*12+3))
    Out.ar(bus=0, source=[comb, comb])

class SynthServer:
    """This class handles synth server operations"""

    def __init__(self) -> None:
        self.running = False
        self.server = None
        self.synths = {}

    @decorators.threaded
    def start_server(self) -> None:
        try:
            self.server = supriya.Server().boot()
            self.server.add_synthdefs(simple_sine)
            self.server.add_synthdefs(sci_fi)
            self.server.sync()
            self.running = True
        except RuntimeError:
            pass
        
    def stop_server(self) -> None:
        self.stop_all_synths()
        if self.server:
            try:
                self.server.quit()
            except TimeoutError:
                pass
        self.running = False

    def start_synth(self, id: int, synth_def) -> None:
        if self.running and id not in self.synths:
            self.synths[id] = self.server.add_synth(synth_def)

    def stop_all_synths(self) -> None:
        for id in list(self.synths):
            self.stop_synth(id)

    def stop_synth(self, id: int) -> None:
        if id in self.synths:
            self.synths[id].free()
            del self.synths[id]

    def update_synth(self, id: int, **kwargs) -> None:
        if id in self.synths:
            self.synths[id].set(**kwargs)

if __name__ == '__main__':
    import wand
    import numpy as np

    wand_sim = wand.WandSimulator()
    server = SynthServer()
    server.start_server()
    id = 0
    while not server.running:
        pass
    server.start_synth(id, sci_fi)

    try:
        while True:
            wand_sim.update_position()
            x, y, r = wand_sim.get_synth_point()
            server.update_synth(id, x=x, y=y, r=r)            
    except KeyboardInterrupt:
        server.stop_server()
    