from dataclasses import dataclass


@dataclass(frozen=True)
class Const:
    n: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Add:
    a: "E"
    b: "E"


@dataclass(frozen=True)
class Mul:
    a: "E"
    b: "E"


E = Const | Var | Add | Mul


def to_string(e: E) -> str:
    """Used to print test results. Don't change it."""
    match e:
        case Const(n):
            return str(n)
        case Var(s):
            return s
        case Add(a, b):
            return f"({to_string(a)} + {to_string(b)})"
        case Mul(a, b):
            return f"({to_string(a)} * {to_string(b)})"


def wrap32(x: int) -> int:
    return (x + 2**31) % 2**32 - 2**31


def rule(e: E) -> E | None:
    """Try every rule once on this node. Return the rewrite, or None if nothing fires."""
    match e:
        case Add(Const(a), Const(b)):
            return Const(wrap32(a + b))
        case Mul(Const(a), Const(b)):
            return Const(wrap32(a * b))
        case Add(Const() as c, x):
            return Add(x, c)
        case Mul(Const() as c, x):
            return Mul(x, c)
        case Add(x, Const(0)):
            return x
        case Mul(x, Const(1)):
            return x
        case Mul(_, Const(0)):
            return Const(0)
        case Add(Add(x, Const(a)), Const(b)):
            return Add(x, Const(wrap32(a + b)))
        case Mul(Mul(x, Const(a)), Const(b)):
            return Mul(x, Const(wrap32(a * b)))
    return None


def simplify(e: E) -> E:
    match e:
        case Add(a, b):
            e = Add(simplify(a), simplify(b))
        case Mul(a, b):
            e = Mul(simplify(a), simplify(b))
    while (r := rule(e)) is not None:
        e = r
    return e
