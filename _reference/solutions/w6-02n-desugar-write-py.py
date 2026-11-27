from dataclasses import dataclass


@dataclass(frozen=True)
class Lit:
    x: float


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Exp2:
    a: object


@dataclass(frozen=True)
class Log2:
    a: object


@dataclass(frozen=True)
class Exp:
    a: object


@dataclass(frozen=True)
class Log:
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
class Sub:
    a: object
    b: object


def to_string(e):
    match e:
        case Lit(x):
            return "%.7g" % x
        case Var(s):
            return s
        case Exp2(a):
            return f"(exp2 {to_string(a)})"
        case Log2(a):
            return f"(log2 {to_string(a)})"
        case Exp(a):
            return f"(exp {to_string(a)})"
        case Log(a):
            return f"(log {to_string(a)})"
        case Add(a, b):
            return f"(add {to_string(a)} {to_string(b)})"
        case Mul(a, b):
            return f"(mul {to_string(a)} {to_string(b)})"
        case Sub(a, b):
            return f"(sub {to_string(a)} {to_string(b)})"


def desugar(e):
    match e:
        case Add(a, b):
            return Add(desugar(a), desugar(b))
        case Mul(a, b):
            return Mul(desugar(a), desugar(b))
        case Exp2(a):
            return Exp2(desugar(a))
        case Log2(a):
            return Log2(desugar(a))
        case Sub(a, b):
            return Add(desugar(a), Mul(desugar(b), Lit(-1.0)))
        case Exp(a):
            return Exp2(Mul(desugar(a), Lit(1.442695)))
        case Log(a):
            return Mul(Log2(desugar(a)), Lit(0.6931472))
    return e
