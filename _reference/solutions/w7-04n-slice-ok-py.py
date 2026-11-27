def slice_ok(s: int, terms: list[tuple[int, int]], size: int) -> bool:
    lo = sum(l for l, _ in terms)
    hi = sum(h for _, h in terms)
    return lo >= 0 and hi + size <= s
