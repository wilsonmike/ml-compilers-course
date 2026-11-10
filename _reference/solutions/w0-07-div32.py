def div32(a: int, b: int) -> int | None:
    if b == 0:
        return None
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return ((q + 2**31) & 0xFFFFFFFF) - 2**31
