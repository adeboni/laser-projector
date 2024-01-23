import math
import time

def clamp(x, min_val, max_val):
    """Clamps x between min_val and max_val"""
    return max(min(max_val, x), min_val)

def cube(x) -> int:
    """Cubes x and clamps it between 0 and 255"""
    return clamp((int)(x * x * x / 255 / 255), 0, 255)

def dots_nightrider() -> list[int]:
    while True:
        dotIndex = math.sin(time.time() * 4) * 5 + 2.5
        yield [cube(255 - 51 * abs(i - dotIndex)) for i in range(6)]

def mouth_pulse() -> list[int]:
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
