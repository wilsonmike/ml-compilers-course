def mod_bounds(r: tuple[int, int], y: int) -> tuple[int, int]:
    lo, hi = r
    if y == 0:
        return (lo, hi)
    if lo // y == hi // y:
        a, b = lo % y, hi % y
        return (min(a, b), max(a, b))
    return (0, y - 1) if y > 0 else (y + 1, 0)
