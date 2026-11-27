def unroll(n: int, body: list[str]) -> list[str]:
    return [line.replace("@", str(r)) for r in range(n) for line in body]
