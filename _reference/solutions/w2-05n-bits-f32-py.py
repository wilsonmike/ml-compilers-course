import struct


def bits_to_f32(bits: str) -> float:
    n = int(bits, 16)
    return struct.unpack("<f", struct.pack("<I", n))[0]
