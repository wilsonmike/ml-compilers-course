from dataclasses import dataclass


@dataclass(frozen=True)
class Lit:
    x: float


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Recip:
    a: object


@dataclass(frozen=True)
class Neg:
    a: object


@dataclass(frozen=True)
class Relu:
    a: object


@dataclass(frozen=True)
class Add:
    a: object
    b: object


@dataclass(frozen=True)
class Mul:
    a: object
    b: object


@dataclass(frozen=True)
class Max:
    a: object
    b: object


@dataclass(frozen=True)
class Sub:
    a: object
    b: object


@dataclass(frozen=True)
class Fdiv:
    a: object
    b: object


def to_string(e):
    match e:
        case Lit(x):
            return "%.7g" % x
        case Var(s):
            return s
        case Recip(a):
            return f"(recip {to_string(a)})"
        case Neg(a):
            return f"(neg {to_string(a)})"
        case Relu(a):
            return f"(relu {to_string(a)})"
        case Add(a, b):
            return f"(add {to_string(a)} {to_string(b)})"
        case Mul(a, b):
            return f"(mul {to_string(a)} {to_string(b)})"
        case Max(a, b):
            return f"(max {to_string(a)} {to_string(b)})"
        case Sub(a, b):
            return f"(sub {to_string(a)} {to_string(b)})"
        case Fdiv(a, b):
            return f"(fdiv {to_string(a)} {to_string(b)})"


def desugar(e):
    match e:
        case Add(a, b):
            return Add(desugar(a), desugar(b))
        case Mul(a, b):
            return Mul(desugar(a), desugar(b))
        case Max(a, b):
            return Max(desugar(a), desugar(b))
        case Recip(a):
            return Recip(desugar(a))
        case Neg(a):
            return Mul(desugar(a), Lit(-1.0))
        case Sub(a, b):
            return Add(desugar(a), desugar(Neg(b)))
        case Relu(a):
            return Max(desugar(a), Lit(0.0))
        case Fdiv(a, b):
            return Mul(desugar(a), Recip(desugar(b)))
    return e
