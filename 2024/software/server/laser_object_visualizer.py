import numpy as np
from matplotlib import pyplot as plt
from laser_objects import *

# X and Y values should range from 0 to 1100

eqns = [ EQN_01, EQN_02, EQN_03, EQN_04, EQN_05, EQN_06, EQN_07, EQN_08, 
         EQN_09, EQN_10, EQN_11, EQN_12, EQN_13, EQN_14, EQN_15, EQN_16, 
         EQN_17, EQN_18, EQN_19, EQN_20, EQN_21, EQN_22, EQN_23, EQN_24, 
         EQN_25, EQN_26, EQN_27, EQN_28, EQN_29, EQN_30, EQN_31, EQN_32, 
         EQN_33, EQN_34, EQN_35, EQN_36 ]
         
letters = [ CHAR_A, CHAR_B, CHAR_C, CHAR_D, CHAR_E, CHAR_F, CHAR_G, CHAR_H,
            CHAR_I, CHAR_J, CHAR_K, CHAR_L, CHAR_M, CHAR_N, CHAR_O, CHAR_P,
            CHAR_Q, CHAR_R, CHAR_S, CHAR_T, CHAR_U, CHAR_V, CHAR_W, CHAR_X,
            CHAR_Y, CHAR_Z, CHAR_0, CHAR_1, CHAR_2, CHAR_3, CHAR_4, CHAR_5, 
            CHAR_6, CHAR_7, CHAR_8, CHAR_9 ]
            
effects = [ EFFECT_BICYCLE_HORN, EFFECT_BIG_GONG, EFFECT_BONGO_DRUMS, 
            EFFECT_BREAKING_GLASS, EFFECT_CAR_HORN, EFFECT_COW, 
            EFFECT_CYMBAL_HIFREQ, EFFECT_CYMBAL_LOFREQ, EFFECT_DRUM, 
            EFFECT_DUCK, EFFECT_FART, EFFECT_FAUCET, EFFECT_FIREWORK, 
            EFFECT_GONG_BELL, EFFECT_KICK_DRUM, EFFECT_SCREAM, EFFECT_SNEEZE, 
            EFFECT_SPRING, EFFECT_TRIANGLE, EFFECT_TROMBONE, EFFECT_TRUMPET, 
            EFFECT_VINTAGE_CAR_HORN, EFFECT_XYLOPHONE ]

graphic_raw = effects
simple = True

x_offset = 2048 - 550
y_offset = 2048 - 550
x, y, c = [], [], []

def print_bounds():
    min_x, max_x = 4095, 0
    min_y, max_y = 4095, 0
    for xx, yy in zip(x, y):
        min_x = min(min_x, xx)
        max_x = max(max_x, xx)
        min_y = min(min_y, yy)
        max_y = max(max_y, yy)
    print(f"X = [{min_x}, {max_x}], Y = [{min_y}, {max_y}]")

if simple:
    for g in graphic_raw:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlim([0, 4095])
        ax.set_ylim([0, 4095])
        ax.set_aspect('equal')
        x, y, c = [], [], []
        for i in range(0, len(g), 2):
            x.append((g[i] & 0x7FFF))
            y.append(g[i+1])
            c.append(True if g[i] & 0x8000 else False)
        for i in range(1, len(x)):
            if c[i]:
                ax.plot([x[i-1] + x_offset, x[i] + x_offset], 
                        [y[i-1] + y_offset, y[i] + y_offset], c='k')
        print_bounds()        
else:
    g = graphic_raw[0]
    fig = plt.figure()
    grid_size = int(np.sqrt(len(g) // 2)) + 1
    axs = [fig.add_subplot(grid_size, grid_size, i + 1) for i in range(len(g) // 2)]
    for i in range(0, len(g), 2):
        x.append((g[i] & 0x7FFF))
        y.append(g[i+1])
        c.append('r' if g[i] & 0x8000 else 'k')
        axs[i // 2].set_xlim([0, 4095])
        axs[i // 2].set_ylim([0, 4095])
        axs[i // 2].set_aspect('equal')
        axs[i // 2].set_title(f'Step {i // 2 + 1}')
        for xx, yy, cc in zip(x, y, c):
            axs[i // 2].plot([xx + x_offset], [yy + y_offset], c=cc, linestyle='', marker='o')
        for j in range(1, len(x)):
            axs[i // 2].plot([x[j - 1] + x_offset, x[j] + x_offset], 
                             [y[j - 1] + y_offset, y[j] + y_offset], c=c[j])
    print_bounds()

plt.show()
