def grads(tape: list) -> list[float]:
    """tape[i] is ('x', v), ('const', v), ('add', a, b) or ('mul', a, b), where a and b index
    earlier entries. Return d(last entry)/d(entry i) for every i."""
    vals = []
    for node in tape:                                  # forward: every value, in order
        op = node[0]
        if op in ('x', 'const'):
            vals.append(node[1])
        elif op == 'add':
            vals.append(vals[node[1]] + vals[node[2]])
        else:
            vals.append(vals[node[1]] * vals[node[2]])
    g = [0.0] * len(tape)
    g[-1] = 1.0                                        # the seed
    for i in range(len(tape) - 1, -1, -1):             # backward: each node passes its gradient down
        op = tape[i][0]
        if op == 'add':
            g[tape[i][1]] += g[i]
            g[tape[i][2]] += g[i]
        elif op == 'mul':
            a, b = tape[i][1], tape[i][2]
            g[a] += g[i] * vals[b]
            g[b] += g[i] * vals[a]
    return g
