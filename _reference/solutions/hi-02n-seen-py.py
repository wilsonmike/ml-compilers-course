from dataclasses import dataclass


@dataclass(eq=False)
class Node:
    op: str
    src: list["Node"]
    arg: int | None = None


def lit(v: int) -> Node:
    return Node("const", [], v)


def chain(k: int) -> Node:
    x = lit(1)
    for _ in range(k):
        x = Node("add", [x, x])
    return x


def walk(n: Node, seen: set[int]) -> int:
    if id(n) in seen:
        return 0
    seen.add(id(n))
    inside = 1
    for s in n.src:
        inside += walk(s, seen)
    return inside


def count_boxes(root: Node) -> int:
    return walk(root, set())
