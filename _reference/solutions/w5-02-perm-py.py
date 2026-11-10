def permute_shape(shape: list[int], order: list[int]) -> list[int]:
    return [shape[p] for p in order]


def src_index(order: list[int], idx: list[int]) -> list[int]:
    src = [0] * len(order)
    for k, p in enumerate(order):
        src[p] = idx[k]
    return src
