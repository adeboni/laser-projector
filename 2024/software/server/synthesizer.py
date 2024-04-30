"""This module controls SuperCollider to create sounds"""

import supercollider

class SynthServer:
    """This class handles synth server operations"""

    def __init__(self) -> None:
        self.running = False
        self.server = None
        self.synths = {}

    def start_server(self) -> None:
        try:
            self.server = supercollider.Server()
            self.running = True
        except:
            pass
        
    def stop_server(self) -> None:
        self.stop_all_synths()
        self.server = None
        self.running = False

    def start_synth(self, id: int) -> None:
        if self.running and id not in self.synths:
            self.synths[id] = supercollider.Synth(self.server, 'scifi')

    def stop_all_synths(self) -> None:
        for id in list(self.synths):
            self.stop_synth(id)

    def stop_synth(self, id: int) -> None:
        if id in self.synths:
            self.synths[id].free()
            del self.synths[id]

    def update_synth(self, id: int, **kwargs) -> None:
        if id in self.synths:
            for k, v in kwargs.items():
                self.synths[id].set(k, v)

if __name__ == '__main__':
    import wand

    wand_sim = wand.WandSimulator()
    id = 0

    server = SynthServer()
    server.start_server()
    server.start_synth(id)

    try:
        while True:
            wand_sim.update_position()
            if wp := wand_sim.get_synth_point():
                x, y, r = wp
                server.update_synth(id, x=x, y=y, r=r)
    except KeyboardInterrupt:
        server.stop_server()
    