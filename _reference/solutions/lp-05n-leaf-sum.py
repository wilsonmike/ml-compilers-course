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

def leaf_sum(e):
    match e:
        case Num(v):
            return v
        case Add(left, right):
            return leaf_sum(left) + leaf_sum(right)
        case Mul(left, right):
            return leaf_sum(left) + leaf_sum(right)
        case _:
            raise TypeError(f"not an expression: {e!r}")
