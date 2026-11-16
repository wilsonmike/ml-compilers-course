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

def chain(n):
    e = Num(1)
    for i in range(n):
        e = Add(Num(1), e)
    return e

def count_nodes(e):
    stack = [e]
    count = 0
    while stack:
        node = stack.pop()
        count += 1
        match node:
            case Num(_):
                pass
            case Add(left, right) | Mul(left, right):
                stack.append(left)
                stack.append(right)
            case _:
                raise TypeError(f"not an expression: {node!r}")
    return count
