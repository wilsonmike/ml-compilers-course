import struct


def to_f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def sum3(a: float, b: float, c: float) -> float:
    return to_f32(to_f32(a + b) + c)
