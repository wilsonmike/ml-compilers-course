def trips(prog: list[tuple[str, int]]) -> list[int]:
    out = []
    for kind, n in prog:
        if kind in ("store", "stage"):
            out.append(n)
        elif kind == "reduce":
            out.append(n - 1)
    return out
