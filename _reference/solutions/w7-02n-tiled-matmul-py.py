def matmul_tiled(a: list[list[float]], b: list[list[float]], th: int, tw: int) -> list[list[float]]:
    n, p, m = len(a), len(b), len(b[0])
    c = [[0.0] * m for _ in range(n)]
    for ib in range(n // th):
        for jb in range(m // tw):
            for k in range(p):
                for i in range(ib * th, ib * th + th):
                    for j in range(jb * tw, jb * tw + tw):
                        c[i][j] = c[i][j] + a[i][k] * b[k][j]
    return c
