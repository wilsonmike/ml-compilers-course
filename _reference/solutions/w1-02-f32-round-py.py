import struct


def f32(x: float) -> float:
    return struct.unpack("f", struct.pack("f", x))[0]


def add32(a: float, b: float) -> float:
    return f32(a + b)
