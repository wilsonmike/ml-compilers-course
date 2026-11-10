from dataclasses import dataclass


@dataclass(frozen=True)
class Leaf:
    value: int


@dataclass(frozen=True)
class Add:
    a: "Leaf | Add"
    b: "Leaf | Add"


def dbl(n: int) -> Leaf | Add:
    """n doublings: one Leaf and n Adds, each Add using the node below it twice."""
    if n == 0:
        return Leaf(1)
    s = dbl(n - 1)
    return Add(s, s)


def dag_size(t: Leaf | Add) -> int:
    # Visited set of id(node): identity, not the structural == and hash of the dataclass.
    # Every node stays alive inside t, so no id is reused while we walk.
    seen: set[int] = set()
    stack = [t]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if isinstance(node, Add):
            stack += [node.a, node.b]
    return len(seen)
