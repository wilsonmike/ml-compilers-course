def divmod32(a: int, b: int) -> tuple[int, int]:
    if b == 0:
        return (-1, a)
    q = a // b
    return ((q + 2**31) % 2**32 - 2**31, a % b)
