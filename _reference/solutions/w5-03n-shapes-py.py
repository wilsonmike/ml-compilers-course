def pad_shape(shape: list[int], pads: list[int]) -> list[int]:
    return [d + pads[2 * k] + pads[2 * k + 1] for k, d in enumerate(shape)]


def expand_src(shape: list[int], idx: list[int]) -> list[int]:
    return [0 if d == 1 else i for d, i in zip(shape, idx)]
