INT_MIN = -(2**31)
INT_MAX = 2**31 - 1


def wrap32(n: int) -> int:
    return (n + 2**31) % 2**32 - 2**31


def add32(a: int, b: int) -> int:
    return wrap32(a + b)


def mul32(a: int, b: int) -> int:
    return wrap32(a * b)


def div32(a: int, b: int) -> int:
    return -1 if b == 0 else wrap32(a // b)


def mod32(a: int, b: int) -> int:
    return a if b == 0 else a % b


EDGES = [0, 1, -1, 2**30, INT_MAX, INT_MIN]


def breaks(before, after) -> list[int]:
    return [x for x in EDGES if before(x) != after(x)]
