def dot(a: list[float], b: list[float]) -> float:
    total = 0.0
    for k in range(len(a)):
        total = total + a[k] * b[k]
    return total


def dot_blocks(a: list[float], b: list[float], block: int) -> float:
    total = 0.0
    for start in range(0, len(a), block):
        for k in range(start, min(start + block, len(a))):
            total = total + a[k] * b[k]
    return total
