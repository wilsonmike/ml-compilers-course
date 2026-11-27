from dataclasses import dataclass


@dataclass
class Node:
    op: str
    src: list
    arg: int | None = None


def lit(v):
    return Node("const", [], v)


def value(n):
    if n.op == "const":
        return n.arg
    a = value(n.src[0])
    b = value(n.src[1])
    if n.op == "add":
        return a + b
    if n.op == "mul":
        return a * b
    if n.op == "sub":
        return a - b
    if n.op == "max":
        return max(a, b)
    raise ValueError(n.op)
