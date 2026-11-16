from dataclasses import dataclass

@dataclass(frozen=True)
class Num:
    value: int

@dataclass(frozen=True)
class Add:
    left: "Expr"
    right: "Expr"

@dataclass(frozen=True)
class Mul:
    left: "Expr"
    right: "Expr"

Expr = Num | Add | Mul

def depth(e):
    match e:
        case Num(_):
            return 1
        case Add(left, right) | Mul(left, right):
            return 1 + max(depth(left), depth(right))
        case _:
            raise TypeError(f"not an expression: {e!r}")
