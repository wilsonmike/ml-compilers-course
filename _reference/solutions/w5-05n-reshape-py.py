def flatten(shape: list[int], idx: list[int]) -> int:
    f = 0
    for s, i in zip(shape, idx):
        f = f * s + i
    return f


def unflatten(shape: list[int], f: int) -> list[int]:
    out = []
    for s in reversed(shape):
        out.insert(0, f % s)
        f = f // s
    return out


def reshape_src(new_shape: list[int], old_shape: list[int], idx: list[int]) -> list[int]:
    return unflatten(old_shape, flatten(new_shape, idx))
