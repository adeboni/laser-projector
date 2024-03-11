import random
import time
from typing import Generator
import numpy as np

MORSE_CODE_DICT = { 
    'A' : '.-', 'B' : '-...',
    'C' : '-.-.', 'D' : '-..', 'E' : '.',
    'F' : '..-.', 'G' : '--.', 'H' : '....',
    'I' : '..', 'J' : '.---', 'K' : '-.-',
    'L' : '.-..', 'M' : '--', 'N' : '-.',
    'O' : '---', 'P' : '.--.', 'Q' : '--.-',
    'R' : '.-.', 'S' : '...', 'T' : '-',
    'U' : '..-', 'V' : '...-', 'W' : '.--',
    'X' : '-..-', 'Y' : '-.--', 'Z' : '--..'
}

def clamp(x, min_val, max_val):
    """Clamps x between min_val and max_val"""
    return max(min(max_val, x), min_val)

def cube(x) -> int:
    """Cubes x and clamps it between 0 and 255"""
    return clamp((int)(x * x * x / 255 / 255), 0, 255)

def dots_nightrider() -> Generator[list[int], None, None]:
    while True:
        dotIndex = np.sin(time.time() * 4) * 5 + 2.5
        yield [cube(255 - 51 * abs(i - dotIndex)) for i in range(6)]

def mouth_pulse() -> Generator[list[int], None, None]:
    output = [0 for _ in range(15)]
    while True:
        mouthColorIndex = np.sin(time.time() * 50 * np.pi / 180) + 1
        mouthRedLevel = cube(255 - 85 * abs(0 - mouthColorIndex))
        mouthWhiteLevel = cube(255 - 85 * abs(1 - mouthColorIndex))
        mouthBlueLevel = cube(255 - 85 * abs(2 - mouthColorIndex))
        for i in range(5):
            output[i] = int((np.sin(time.time() * 4) + 1) * 128 * mouthRedLevel / 255)
            output[i + 5] = int((np.sin(time.time() * 4) + 1) * 128 * mouthWhiteLevel / 255)
            output[i + 10] = int((np.sin(time.time() * 4) + 1) * 128 * mouthBlueLevel / 255)
        yield output

def motors_spin() -> Generator[list[int], None, None]:
    current_pattern = [255 * random.randint(0, 1) for x in range(3)]
    last_update = time.time()
    while True:
        if time.time() - last_update > 3:
            current_pattern = [255 * random.randint(0, 1) for x in range(3)]
            last_update = time.time()
        yield current_pattern

def expand_morse_code(text: str) -> list[int]:
    result = []
    for char in text:
        if char == ' ':
            result.extend([0] * 4)
        elif char in MORSE_CODE_DICT:
            for morse_char in MORSE_CODE_DICT[char]:
                if morse_char == '.':
                    result.extend([255] * 1)
                elif morse_char == '-':
                    result.extend([255] * 3)
                result.extend([0] * 1)
            result.extend([0] * 3)
    result.extend([0] * 7)
    return result

def lamp_morse_code() -> Generator[int, None, None]:
    time_unit = 0.2
    phrases = ["MATH CAMP", "BURNING MAN", "SIERPINSKI"]
    current_phrase_index = 0
    current_phrase = expand_morse_code(phrases[current_phrase_index])
    last_start_time = time.time()
    while True:
        phrase_time_index = int((time.time() - last_start_time) / time_unit)
        if phrase_time_index < len(current_phrase):
            yield current_phrase[phrase_time_index]
        else:
            last_start_time = time.time()
            current_phrase_index = (current_phrase_index + 1) % len(phrases)
            current_phrase = expand_morse_code(phrases[current_phrase_index])
