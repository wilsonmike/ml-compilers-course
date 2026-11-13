def per_thread(accesses: list[tuple]) -> int:
    """accesses: (S, lo, hi, size) each, S None if t isn't a plain multiple. The shared S when every access stays in its slice, else 0."""
    if not accesses:
        return 0
    S = accesses[0][0]
    if S is None or S <= 0:
        return 0
    for s, lo, hi, size in accesses:
        if s != S or lo < 0 or hi + size > S:
            return 0
    return S
