"""Defines a LaserPoint class and helper functions"""

def bytes_to_xy(b0: int, b1: int, b2: int) -> list[int]:
    """Converts three 8 bit values to two 12 bit values"""
    return [b0 << 4 | b1 >> 4, (b1 & 0x0f) << 8 | b2]

def xy_to_bytes(x: int, y: int) -> list[int]:
    """Converts two 12 bit values to three 8 bit values for sACN"""
    return [x >> 4, (x & 0xf) << 4 | y >> 8, y & 0xff]

class LaserPoint:
    def __init__(self, id: int, x: int = 0, y: int = 0, r: int = 0, g: int = 0, b: int = 0):
        self.id = id
        self.x = x
        self.y = y
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def from_bytes(cls, id: int, bytes: list[int]):
        x, y = bytes_to_xy(*bytes[:3])
        r, g, b = bytes[3:]
        return cls(id, x, y, r, g, b)

    def get_bytes(self) -> list[int]:
        return xy_to_bytes(self.x, self.y) + [self.r, self.g, self.b]
    
    def __repr__(self):
        return f'ID: {self.id}, Point: [{self.x}, {self.y}], Color: [{self.r}, {self.g}, {self.b}]'
    