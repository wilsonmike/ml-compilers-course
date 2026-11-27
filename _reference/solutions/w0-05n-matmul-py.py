def matmul(a, b, rows, mid, cols):
    c = [0] * (rows * cols)
    for i in range(rows):
        for j in range(cols):
            total = 0
            for k in range(mid):
                total = total + a[i * mid + k] * b[k * cols + j]
            c[i * cols + j] = total
    return c
