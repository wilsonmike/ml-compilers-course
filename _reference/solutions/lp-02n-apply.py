def apply(op: str, a: int, b: int) -> int:
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "min":
        if a < b:
            return a
        return b
    return 0
