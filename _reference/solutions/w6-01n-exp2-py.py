import math

COEFFS = [1.5252734e-05, 0.0001540353, 0.0013333558, 0.009618129, 0.05550411, 0.2402265, 0.6931472, 1.0]


def small(f: float) -> float:
    acc = 0.0
    for c in COEFFS:
        acc = acc * f + c
    return acc


def pow2(n: int) -> float:
    return math.ldexp(1.0, n)


def exp2(x: float) -> float:
    n = math.floor(x + 0.5)
    f = x - n
    return small(f) * pow2(n)
