"""Simulates a UI board"""

import tkinter as tk
import sacn

def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

class MainApp(tk.Tk):
    """Class representing the GUI"""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title('UI Simulator')
        self.geometry('900x530')
        self.resizable(False, False)
        self._setup_labels()

        self.sacn = sacn.sACNreceiver()
        @self.sacn.listen_on('universe', universe=1)
        def _callback(packet):
            self._update_display(0, packet)
            self._update_display(1, packet)
            self._update_mouth(packet)
            self._update_dots(packet)
            self._update_motors_lamp(packet)
            self._update_buttons(packet)

        self.sacn.start()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_labels(self) -> None:
        self.display_0_frame = tk.Frame(self)
        self.display_0_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.display_1_frame = tk.Frame(self)
        self.display_1_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.display_0 = []
        for r in range(2):
            for c in range(40):
                self.display_0.append(tk.Label(self.display_0_frame, text=' ', font=('Courier', 18), bg='blue', fg='white', highlightthickness=1, highlightbackground='white'))
                self.display_0[-1].grid(row=r, column=c)

        self.display_1 = []
        for r in range(2):
            for c in range(40):
                self.display_1.append(tk.Label(self.display_1_frame, text=' ', font=('Courier', 18), bg='blue', fg='white', highlightthickness=1, highlightbackground='white'))
                self.display_1[-1].grid(row=r, column=c)

        self.mouth_frame = tk.Frame(self)
        self.mouth_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.mouth = []
        for r in range(15):
            self.mouth.append(tk.Label(self.mouth_frame, font=('Courier', 2), bg='black', highlightthickness=1, highlightbackground='white'))
            self.mouth[-1].pack(side=tk.TOP, fill=tk.X)

        self.dots_frame = tk.Frame(self)
        self.dots_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.dots = []
        for c in range(6):
            self.dots.append(tk.Label(self.dots_frame, text=f'  D{c}  ', font=('Courier', 18), bg='black', fg='blue', highlightthickness=1, highlightbackground='white'))
            self.dots[-1].grid(row=0, column=c)

        self.motors_lamp_frame = tk.Frame(self)
        self.motors_lamp_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.motors_lamp = []
        for c in range(3):
            self.motors_lamp.append(tk.Label(self.motors_lamp_frame, text=f'  M{c}  ', font=('Courier', 18), bg='black', fg='blue', highlightthickness=1, highlightbackground='white'))
            self.motors_lamp[-1].grid(row=0, column=c)
        self.motors_lamp.append(tk.Label(self.motors_lamp_frame, text=f' LAMP ', font=('Courier', 18), bg='black', fg='blue', highlightthickness=1, highlightbackground='white'))
        self.motors_lamp[-1].grid(row=0, column=3)

        self.buttons_frame = tk.Frame(self)
        self.buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.buttons = []
        for c in range(7):
            self.buttons.append(tk.Label(self.buttons_frame, text=f'  B{c}  ', font=('Courier', 18), bg='black', fg='blue', highlightthickness=1, highlightbackground='white'))
            self.buttons[-1].grid(row=0, column=c)
            
    def _on_closing(self) -> None:
        self.sacn.stop()
        self.destroy()

    def _update_display(self, display_num: int, packet) -> None:
        if display_num == 0:
            for i in range(80):
                self.display_0[i].config(text=chr(packet.dmxData[i]))
        elif display_num == 1:
            for i in range(80):
                self.display_1[i].config(text=chr(packet.dmxData[i + 80]))

    def _update_mouth(self, packet) -> None:
        label_indexes = [0, 3, 6, 9, 12, 1, 4, 7, 10, 13, 2, 5, 8, 11, 14]        
        for i in range(15):
            data = packet.dmxData[i + 160]
            if i // 5 == 0: # red
                color = rgb_to_hex(data, 0, 0)
            elif i // 5 == 1: # white
                color = rgb_to_hex(data, data, data)
            else: # blue
                color = rgb_to_hex(0, 0, data)
            self.mouth[label_indexes[i]].config(bg=color)

    def _update_dots(self, packet) -> None:
        for i in range(6):
            data = packet.dmxData[i + 175]
            self.dots[i].config(bg=rgb_to_hex(data, data, data))

    def _update_motors_lamp(self, packet) -> None:
        for i in range(4):
            data = packet.dmxData[i + 181]
            self.motors_lamp[i].config(bg=rgb_to_hex(data, data, data))

    def _update_buttons(self, packet) -> None:
        for i in range(7):
            data = packet.dmxData[i + 185]
            self.buttons[i].config(bg=rgb_to_hex(data, data, data))

if __name__ == '__main__':
    MainApp().mainloop()
