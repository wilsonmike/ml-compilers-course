import math
import struct


def f32(x: float) -> float:
    # "<f" is the standard 4-byte f32. It rounds to nearest even, but raises OverflowError
    # when the rounded value would be infinite, where C (and the spec) give an infinity.
    try:
        return struct.unpack("<f", struct.pack("<f", x))[0]
    except OverflowError:
        return math.copysign(math.inf, x)


def add32(a: float, b: float) -> float:
    return f32(a + b)
