from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    name: str
    srcs: tuple[str, ...]


def topo(graph: list[Node], root: str) -> list[str]:
    by_name = {n.name: n for n in graph}
    seen: set[str] = set()
    out: list[str] = []
    stack = [(root, False)]
    while stack:
        name, finished = stack.pop()
        if finished:
            out.append(name)
            continue
        if name in seen:
            continue
        seen.add(name)
        stack.append((name, True))
        for s in reversed(by_name[name].srcs):
            stack.append((s, False))
    return out
