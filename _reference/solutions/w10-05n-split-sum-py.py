def split_sum(xs: list[float], n: int) -> float:
    s = len(xs) // n
    parts = []
    for d in range(n):
        p = 0.0
        for e in range(s):
            p = p + xs[d * s + e]
        parts.append(p)
    total = parts[0]
    for p in parts[1:]:
        total = total + p
    return total
