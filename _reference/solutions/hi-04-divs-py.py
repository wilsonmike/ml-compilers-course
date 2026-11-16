def divs(a: int, b: int) -> tuple[int, int, int, int]:
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    r = a - b * q
    return (q, r, a // b, a % b)
