def outcome(size: int, parses: bool, nodes: int, edges: int, valid: bool, cost: int, got: int, want: int) -> str:
    if size > 4096:
        return "OVERBUDGET"
    if not parses:
        return "REJECTED"
    if nodes >= 100 or edges >= 300:
        return "OVERBUDGET"
    if not valid:
        return "REJECTED"
    if cost >= 1000000:
        return "OVERBUDGET"
    return "MATCH" if got == want else "MISMATCH"
