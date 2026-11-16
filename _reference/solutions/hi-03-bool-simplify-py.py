from dataclasses import dataclass


@dataclass(frozen=True)
class T:
    pass


@dataclass(frozen=True)
class F:
    pass


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Not:
    a: object


@dataclass(frozen=True)
class And:
    a: object
    b: object


@dataclass(frozen=True)
class Or:
    a: object
    b: object


def to_string(e) -> str:
    match e:
        case T():
            return "T"
        case F():
            return "F"
        case Var(name):
            return name
        case Not(a):
            return f"(not {to_string(a)})"
        case And(a, b):
            return f"({to_string(a)} and {to_string(b)})"
        case Or(a, b):
            return f"({to_string(a)} or {to_string(b)})"


def rule(e):
    match e:
        case Not(T()):
            return F()
        case Not(F()):
            return T()
        case Not(Not(x)):
            return x
        case And(x, T()) | And(T(), x):
            return x
        case And(_, F()) | And(F(), _):
            return F()
        case Or(x, F()) | Or(F(), x):
            return x
        case Or(_, T()) | Or(T(), _):
            return T()
    return None


def simplify(e):
    match e:
        case Not(a):
            e = Not(simplify(a))
        case And(a, b):
            e = And(simplify(a), simplify(b))
        case Or(a, b):
            e = Or(simplify(a), simplify(b))
    while True:
        new = rule(e)
        if new is None:
            return e
        e = new
