from dataclasses import dataclass


@dataclass
class Permute:
    order: list[int]

@dataclass
class Expand:
    shape: list[int]

@dataclass
class Shrink:
    offsets: list[int]

Mov = Permute | Expand | Shrink


def src(op: Mov, idx: list[int]) -> list[int]:
    match op:
        case Permute(order):
            return [idx[order.index(a)] for a in range(len(order))]
        case Expand(shape):
            return [0 if s == 1 else i for s, i in zip(shape, idx)]
        case Shrink(offsets):
            return [i + o for i, o in zip(idx, offsets)]
