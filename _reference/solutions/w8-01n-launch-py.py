def launch(blocks: int, size: int, x: list[int]) -> list[int]:
    out = [0] * len(x)
    for b in range(blocks):
        for t in range(size):
            i = size * b + t
            out[i] = x[i] * 2
    return out
