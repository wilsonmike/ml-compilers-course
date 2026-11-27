def im2col(x: list, k: int) -> list:
    rows = []
    for i in range(len(x) - k + 1):
        row = []
        for j in range(k):
            row.append(x[i + j])
        rows.append(row)
    return rows
