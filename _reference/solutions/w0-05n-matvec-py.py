def matvec(m, rows, cols, v):
    out = []
    for r in range(rows):
        total = 0
        for c in range(cols):
            total = total + m[r * cols + c] * v[c]
        out.append(total)
    return out
