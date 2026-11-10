from dataclasses import dataclass
from typing import Callable


# A toy node. Don't change it. eq=False makes == and hash() compare identity, like OCaml's ==.
@dataclass(eq=False)
class Node:
    id: int
    op: str
    src: list["Node"]


def create() -> Callable[[str, list[Node]], Node]:
    table: dict[tuple[str, tuple[int, ...]], Node] = {}

    def make(op: str, src: list[Node]) -> Node:
        key = (op, tuple(n.id for n in src))
        node = table.get(key)
        if node is None:
            node = Node(len(table), op, src)  # every entry is a distinct node, so len(table) is the next id
            table[key] = node
        return node

    return make
