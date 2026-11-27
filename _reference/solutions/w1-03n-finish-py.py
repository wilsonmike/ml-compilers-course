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


def to_string(e):
    match e:
        case Const(n):
            return str(n)
        case Var(s):
            return s
        case Add(a, b):
            return f"({to_string(a)} + {to_string(b)})"
        case Mul(a, b):
            return f"({to_string(a)} * {to_string(b)})"


def wrap32(x):
    return (x + 2**31) % 2**32 - 2**31


def rule(e):
    match e:
        case Add(Const(a), Const(b)):
            return Const(wrap32(a + b))
        case Mul(Const(a), Const(b)):
            return Const(wrap32(a * b))
        case Add(x, Const(0)):
            return x
        case Mul(x, Const(1)):
            return x
        case Add(Add(x, Const(a)), Const(b)):
            return Add(x, Const(wrap32(a + b)))
    return None


def simplify(e):
    match e:
        case Add(a, b):
            e = Add(simplify(a), simplify(b))
        case Mul(a, b):
            e = Mul(simplify(a), simplify(b))
    r = rule(e)
    while r is not None:
        e = r
        r = rule(e)
    return e
