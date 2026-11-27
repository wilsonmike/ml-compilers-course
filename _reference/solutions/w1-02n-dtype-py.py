def result_dtype(op: str, a: str, b: str) -> str:
    if op in ("add", "mul", "max", "xor"):
        return a if a == b else "rejected"
    if op == "cmplt":
        return "bool" if a == b else "rejected"
    if op in ("div", "mod", "shl"):
        return "i32" if a == "i32" and b == "i32" else "rejected"
    return "rejected"
