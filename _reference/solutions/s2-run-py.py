def apply(op: str, a: int, b: int) -> int:
    if op == "add":
        return a + b
    if op == "mul":
        return a * b
    if op == "max":
        return max(a, b)
    raise ValueError(op)


def run(prog: list[tuple[str, str, int | str, int | str]]) -> int:
    env: dict[str, int] = {}
    for name, op, x, y in prog:
        a = env[x] if isinstance(x, str) else x
        b = env[y] if isinstance(y, str) else y
        env[name] = apply(op, a, b)
    return env[prog[-1][0]]
