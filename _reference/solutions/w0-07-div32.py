def div32(a: int, b: int) -> int:
    if b == 0:
        return -1
    return (a // b + 2**31) % 2**32 - 2**31
