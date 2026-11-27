def to_i8(x: int) -> int:
    return ((x + 128) & 255) - 128
