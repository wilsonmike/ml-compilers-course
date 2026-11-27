def depth_in(order: list[str], opens: set[str]) -> int:
    best = 0
    for d, r in enumerate(order, start=1):
        if r in opens:
            best = d
    return best
