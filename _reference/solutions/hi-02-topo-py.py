def topo(g: dict[str, list[str]], root: str) -> list[str]:
    started: set[str] = set()
    out: list[str] = []
    stack = [(root, False)]
    while stack:
        item, ready = stack.pop()
        if ready:
            out.append(item)
        elif item not in started:
            started.add(item)
            stack.append((item, True))
            for part in reversed(g.get(item, [])):
                stack.append((part, False))
    return out
