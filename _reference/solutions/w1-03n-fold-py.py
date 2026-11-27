def wrap32(x):
    return (x + 2**31) % 2**32 - 2**31


def fold(op, a, b):
    if op == "add":
        return wrap32(a + b)
    if op == "mul":
        return wrap32(a * b)
    if op == "div":
        return -1 if b == 0 else wrap32(a // b)
    return 0
