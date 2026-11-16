def fixpoint(f, x):
    count = 0
    while True:
        y = f(x)
        if y == x:
            return (x, count)
        x = y
        count += 1
