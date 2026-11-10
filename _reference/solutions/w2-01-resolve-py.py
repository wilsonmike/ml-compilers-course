from dataclasses import dataclass


@dataclass(frozen=True)
class Buffer:
    n: int  # a whole buffer of n elements


@dataclass(frozen=True)
class Shrink:
    parent: "View"  # shrink parent off shape=[k]
    off: int
    k: int


@dataclass(frozen=True)
class Elem:
    parent: "View"  # shrink parent off shape=[]
    off: int


View = Buffer | Shrink | Elem


def step(parent: View, off: int, k: int) -> tuple[int, int]:
    start, length = resolve(parent)
    if off < 0 or off + k > length:
        raise ValueError("out of bounds")
    return (start + off, k)


def resolve(v: View) -> tuple[int, int]:
    match v:
        case Buffer(n):
            return (0, n)
        case Shrink(p, off, k):
            return step(p, off, k)
        case Elem(p, off):
            return step(p, off, 1)
