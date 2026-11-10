def mod_bounds(r: tuple[int, int], m: int) -> tuple[int, int]:
    lo, hi = r
    if lo >= 0:
        return (0, min(m - 1, hi))
    if hi < 0:
        return (max(-(m - 1), lo), 0)
    return (max(-(m - 1), lo), min(m - 1, hi))
