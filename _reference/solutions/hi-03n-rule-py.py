from dataclasses import dataclass


@dataclass(frozen=True)
class Const:
    n: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Add:
    a: object
    b: object


@dataclass(frozen=True)
class Mul:
    a: object
    b: object


def show(e) -> str:
    match e:
        case Const(n):
            return str(n)
        case Var(name):
            return name
        case Add(a, b):
            return f"({show(a)} + {show(b)})"
        case Mul(a, b):
            return f"({show(a)} * {show(b)})"


def rule(e):
    match e:
        case Add(x, Const(0)):
            return x
        case Mul(x, Const(1)):
            return x
        case Add(Const(m), Const(n)):
            return Const(m + n)
        case Mul(Const(m), Const(n)):
            return Const(m * n)
    return None
