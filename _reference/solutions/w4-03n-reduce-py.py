from dataclasses import dataclass


@dataclass(frozen=True)
class Vec:
    buf: str

@dataclass(frozen=True)
class Bcast:
    value: float

@dataclass(frozen=True)
class Add:
    a: "VExp"
    b: "VExp"

@dataclass(frozen=True)
class Mul:
    a: "VExp"
    b: "VExp"

VExp = Vec | Bcast | Add | Mul


@dataclass(frozen=True)
class Load:
    buf: str
    idx: str

@dataclass(frozen=True)
class Const:
    value: float

@dataclass(frozen=True)
class SAdd:
    a: "SExp"
    b: "SExp"

@dataclass(frozen=True)
class SMul:
    a: "SExp"
    b: "SExp"

SExp = Load | Const | SAdd | SMul


def show(s: SExp) -> str:
    match s:
        case Load(b, i):
            return f"{b}[{i}]"
        case Const(c):
            return f"{c:g}"
        case SAdd(a, b):
            return f"({show(a)} + {show(b)})"
        case SMul(a, b):
            return f"({show(a)} * {show(b)})"


def at(e: VExp, i: str) -> SExp:
    match e:
        case Vec(b):
            return Load(b, i)
        case Bcast(c):
            return Const(c)
        case Add(a, b):
            return SAdd(at(a, i), at(b, i))
        case Mul(a, b):
            return SMul(at(a, i), at(b, i))


def lower_reduce(e: VExp, n: int) -> str:
    seed = show(at(e, "0"))
    step = show(at(e, "r+1"))
    return f"acc = {seed}; for r < {n - 1}: acc = acc + {step}"
