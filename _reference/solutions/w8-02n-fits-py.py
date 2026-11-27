def fits(c: int, digits: list[tuple[int, int]]) -> bool:
    most = sum(d * m for d, m in digits)
    return c > most
