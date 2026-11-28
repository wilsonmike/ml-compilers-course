def smallest_work(n: int, copy: int) -> int:
    w = 1
    while w + n * copy >= n * w:
        w += 1
    return w
