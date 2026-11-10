def wrap32(x: int) -> int:
    return (x + 2**31) % 2**32 - 2**31


def div32(a: int, b: int) -> int | None:
    if b == 0:
        return None
    q = abs(a) // abs(b)  # magnitudes: floor and truncation agree here
    return wrap32(q if (a < 0) == (b < 0) else -q)
