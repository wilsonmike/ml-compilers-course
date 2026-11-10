def decode_i32(data: bytes) -> list[int]:
    """Little-endian 32-bit two's complement integers, back to back."""
    if len(data) % 4:
        raise ValueError("not a whole number of i32")
    out = []
    for i in range(0, len(data), 4):
        u = data[i] | data[i + 1] << 8 | data[i + 2] << 16 | data[i + 3] << 24
        out.append(u - (1 << 32) if u >= 1 << 31 else u)
    return out
