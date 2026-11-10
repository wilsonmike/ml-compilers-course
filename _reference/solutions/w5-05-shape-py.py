from dataclasses import dataclass


@dataclass
class Reshape:
    shape: list[int]

@dataclass
class Permute:
    order: list[int]

@dataclass
class Pad:
    pads: list[int]  # left and right for each axis: [l0, r0, l1, r1, ...]

@dataclass
class Expand:
    shape: list[int]

@dataclass
class Reduce:
    m: int  # drops the first m axes

Op = Reshape | Permute | Pad | Expand | Reduce


def shape_after(shape: list[int], ops: list[Op]) -> list[int]:
    for op in ops:
        match op:
            case Reshape(s) | Expand(s):
                shape = list(s)
            case Permute(order):
                shape = [shape[p] for p in order]
            case Pad(pads):
                shape = [d + pads[2 * k] + pads[2 * k + 1] for k, d in enumerate(shape)]
            case Reduce(m):
                shape = shape[m:]
    return shape
