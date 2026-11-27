def wrap32(x):
    return (x + 2**31) % 2**32 - 2**31


def prod32(xs):
    acc = xs[0]
    for y in xs[1:]:
        acc = wrap32(acc * y)
    return acc
