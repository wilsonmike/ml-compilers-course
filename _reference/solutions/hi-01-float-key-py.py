import struct


def float_key(x: float) -> bytes:
    return struct.pack(">d", x)
