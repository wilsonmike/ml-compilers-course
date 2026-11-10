import math
import struct


def f32(x: float) -> float:
    """Round a Python float (a 64-bit double) to the nearest f32."""
    try:
        return struct.unpack("f", struct.pack("f", x))[0]
    except OverflowError:  # finite but past the f32 range: rounds to infinity
        return math.copysign(math.inf, x)


def sum32(xs: list[float]) -> float:
    if not xs:
        raise ValueError("sum32: empty")
    acc = xs[0]
    for y in xs[1:]:
        acc = f32(acc + y)
    return acc
