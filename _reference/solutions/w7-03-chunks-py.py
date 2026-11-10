def chunks(n: int, t: int) -> list[tuple[int, int]]:
    """One contiguous (lo, hi) range per thread."""
    m = max(1, min(t, n))
    return [(n * k // m, n * (k + 1) // m) for k in range(m)]
