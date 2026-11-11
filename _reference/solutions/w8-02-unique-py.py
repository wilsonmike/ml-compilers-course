def unique(digits: list[tuple[int, int]]) -> bool:
    """digits: (coefficient, largest value). True when the offset is a unique mixed-radix number."""
    ds = sorted(digits, key=lambda d: -d[0])
    for k, (c, m) in enumerate(ds):
        if m == 0:
            continue
        if c <= sum(c2 * m2 for c2, m2 in ds[k + 1:]):
            return False
    return True
