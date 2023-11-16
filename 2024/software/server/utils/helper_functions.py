"""This module contains helper functions"""

def divide_chunks(l: list, n: int) -> list:
    """Splits a list into chunks of size n"""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def bytes_to_xy(b0: int, b1: int, b2: int) -> list[int]:
    """Converts three 8 bit values to two 12 bit values"""
    return [b0 << 4 | b1 >> 4, (b1 & 0x0f) << 8 | b2]

def xy_to_bytes(x: int, y: int) -> list[int]:
    """Converts two 12 bit values to three 8 bit values for sACN"""
    return [x >> 4, (x & 0xf) << 4 | y >> 8, y & 0xff]
