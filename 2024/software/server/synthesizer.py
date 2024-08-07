"""This module controls SuperCollider to create sounds"""

import supercollider
import threading

class SynthServer:
    """This class handles synth server operations"""

    def __init__(self, wands=None) -> None:
        self.running = False
        self.server = None
        self.synths = {}
        self.wands = wands
        self.update_thread = threading.Thread(target=self._update_thread, daemon=True)
        self._update_event = threading.Event()
        self.connecting = False
        self.connect_thread = threading.Thread(target=self._connect_thread, daemon=True)
        self._connect_event = threading.Event()

    def _update_thread(self) -> None:
        while self.running:
            if self.wands:
                for wand in list(self.wands):
                    if (w := self.wands[wand]) and (sp := w.get_synth_point()):
                        self.update_synth(wand, x=sp[0], y=sp[1], r=sp[2])
            self._update_event.wait(0.02)

    def _connect_thread(self) -> None:
        while self.connecting:
            try:
                self.server = supercollider.Server()
                self.running = True
                self.update_thread.start()
                return
            except:
                self._connect_event.wait(2)

    def start_server(self) -> None:
        if not self.running and not self.connecting:
            self.connecting = True
            self.connect_thread.start()
        
    def stop_server(self) -> None:
        if self.connecting:
            self.connecting = False
            self._connect_event.set()
            self.connect_thread.join()
        if self.running:
            self.stop_all_synths()
            self.server = None
            self.running = False
            self._update_event.set()
            self.update_thread.join()

    def start_synth(self, id) -> None:
        if self.running and id not in self.synths:
            self.synths[id] = supercollider.Synth(self.server, 'scifi')

    def stop_all_synths(self) -> None:
        for id in list(self.synths):
            self.stop_synth(id)

    def stop_synth(self, id) -> None:
        if id in self.synths:
            self.synths[id].free()
            del self.synths[id]

    def update_synth(self, id, **kwargs) -> None:
        if id in self.synths:
            for k, v in kwargs.items():
                self.synths[id].set(k, v)

if __name__ == '__main__':
    import wand
    import time

    wands = { -1: wand.WandSimulator() }
    server = SynthServer(wands)
    server.start_server()
    time.sleep(2)
    if not server.running:
        print('Failed to connect to server!')
        quit()
    server.start_synth(-1)

    try:
        time.sleep(60)
    except KeyboardInterrupt:
        server.stop_server()
    