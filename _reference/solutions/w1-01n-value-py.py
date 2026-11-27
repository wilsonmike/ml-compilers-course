from dataclasses import dataclass


@dataclass(eq=False)
class Node:
    op: str
    src: list["Node"]
    arg: int | None = None


def lit(v: int) -> Node:
    return Node("const", [], v)


def value(n: Node) -> int:
    if n.op == "const":
        return n.arg
    a = value(n.src[0])
    b = value(n.src[1])
    if n.op == "add":
        return a + b
    if n.op == "mul":
        return a * b
    raise ValueError("not a node this toy knows")
