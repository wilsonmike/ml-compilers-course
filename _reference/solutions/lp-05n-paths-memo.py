calls = []
memo = {}

def paths(r, c):
    calls.append((r, c))
    if (r, c) in memo:
        return memo[(r, c)]
    if r == 0 or c == 0:
        return 1
    answer = paths(r - 1, c) + paths(r, c - 1)
    memo[(r, c)] = answer
    return answer

def calls_for(r, c):
    memo.clear()
    calls.clear()
    paths(r, c)
    return len(calls)
