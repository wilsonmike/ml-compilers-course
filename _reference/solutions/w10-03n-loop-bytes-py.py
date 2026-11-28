def loop_bytes(devices: int, bufs: list[tuple[int, int, bool, int]]) -> int:
    total = 0
    for size, elem, written, stride in bufs:
        if stride == 0:
            total += devices * size * elem
        else:
            total += devices * stride * elem * (2 if written else 1)
    return total
