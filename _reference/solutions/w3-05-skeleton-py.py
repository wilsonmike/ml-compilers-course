def skeleton(loops: list[tuple[str, str]], body: str) -> str:
    n = len(loops)
    pad = lambda d: "  " * d
    heads = [f"{pad(d)}for (int32_t {v} = 0; {v} < {b}; {v}++) {{" for d, (v, b) in enumerate(loops)]
    closes = [pad(d) + "}" for d in reversed(range(n))]
    return "\n".join(heads + [pad(n) + body] + closes)
