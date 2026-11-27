def apply(op: str, a: int, b: int) -> int:
    if op == "add":
        return a + b
    if op == "mul":
        return a * b
    if op == "max":
        return max(a, b)
    raise ValueError(op)
