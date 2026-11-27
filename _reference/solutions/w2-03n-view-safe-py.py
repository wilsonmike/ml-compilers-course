def view_safe(bounds: tuple[int, int], n: int, k: int) -> bool:
    lo, hi = bounds
    last_start = n - k
    return lo >= 0 and hi <= last_start
