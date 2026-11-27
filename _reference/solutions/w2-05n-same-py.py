import math
import struct


def same_f32(want: list[float], got: list[float]) -> bool:
    if len(want) != len(got):
        return False
    for a, b in zip(want, got):
        if math.isnan(a) and math.isnan(b):
            continue
        if struct.pack("<f", a) != struct.pack("<f", b):
            return False
    return True
