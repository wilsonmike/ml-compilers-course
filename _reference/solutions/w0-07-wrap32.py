def wrap32(x: int) -> int:
    return ((x + 2**31) & 0xFFFFFFFF) - 2**31
