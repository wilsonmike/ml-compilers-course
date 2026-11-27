def backward(tape, val):
    n = len(tape)
    g = [0.0] * n
    g[n - 1] = 1.0
    for i in range(n - 1, -1, -1):
        e = tape[i]
        if e[0] == 'add':
            g[e[1]] += g[i]
            g[e[2]] += g[i]
        elif e[0] == 'mul':
            g[e[1]] += g[i] * val[e[2]]
            g[e[2]] += g[i] * val[e[1]]
    return g
