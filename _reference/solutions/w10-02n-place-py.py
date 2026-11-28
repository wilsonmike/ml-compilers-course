def place(n: int, size: int, accesses: list[tuple[bool, int, int, int]]) -> int:
    strides = {s for _, s, _, _ in accesses}
    s = accesses[0][1]
    fits = all(s >= 1 and lo >= 0 and hi + 1 <= s for _, s, lo, hi in accesses)
    if fits and len(strides) == 1 and n * s <= size:
        return s
    if any(w for w, _, _, _ in accesses):
        return -1
    return 0
