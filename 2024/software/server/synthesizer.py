"""This module controls SuperCollider to create sounds"""

import supriya
from supriya.ugens import *

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
        self.synth = None

    def start(self, synth_def) -> None:
        self.server = supriya.Server().boot()
        self.server.add_synthdefs(synth_def)
        self.server.sync()
        self.synth = self.server.add_synth(synth_def)

    def stop(self) -> None:
        if self.synth:
            self.synth.free()
            self.synth = None
        if self.server:
            self.server.quit()
            self.server = None

    def update_synth(self, **kwargs) -> None:
        self.synth.set(**kwargs)
