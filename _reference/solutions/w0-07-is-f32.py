import math
import struct


def is_f32(x: float) -> bool:
    if math.isnan(x) or math.isinf(x):
        return True
    try:
        y = struct.unpack('<f', struct.pack('<f', x))[0]
    except OverflowError:
        return False
    return y == x
