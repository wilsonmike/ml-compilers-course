from dataclasses import dataclass

@dataclass(frozen=True)
class Num:
    value: int

@dataclass(frozen=True)
class Add:
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class Sub:
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class Mul:
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class Neg:
    inner: "Expr"

Expr = Num | Add | Sub | Mul | Neg

def evaluate(e):
    match e:
        case Num(v):
            return v
        case Add(left, right):
            return evaluate(left) + evaluate(right)
        case Sub(left, right):
            return evaluate(left) - evaluate(right)
        case Mul(left, right):
            return evaluate(left) * evaluate(right)
        case Neg(inner):
            return -evaluate(inner)
        case _:
            raise TypeError(f"not an expression: {e!r}")
