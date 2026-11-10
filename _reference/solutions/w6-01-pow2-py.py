import struct


def pow2(n: int) -> float:
    """2^n for -126 <= n <= 127, built from the f32 bit pattern."""
    bits = (n + 127) << 23
    return struct.unpack('<f', struct.pack('<i', bits))[0]
