from dataclasses import dataclass


@dataclass(eq=False)
class Node:
    id: int
    op: str
    src: list["Node"]


def create():
    table = {}

    def make(op: str, src: list[Node]) -> Node:
        key = (op, tuple(n.id for n in src))
        if key in table:
            return table[key]
        node = Node(len(table), op, src)
        table[key] = node
        return node

    return make
