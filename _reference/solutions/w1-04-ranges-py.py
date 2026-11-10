from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    lo: int
    hi: int


INT_MIN = -(2**31)
INT_MAX = 2**31 - 1
FULL = Range(INT_MIN, INT_MAX)


def fits(r: Range) -> Range:
    """Python ints are exact, so r is the true interval. If it leaves i32, the real op could wrap."""
    return FULL if r.lo < INT_MIN or r.hi > INT_MAX else r


def add_range(a: Range, b: Range) -> Range:
    return fits(Range(a.lo + b.lo, a.hi + b.hi))


def mul_range(a: Range, b: Range) -> Range:
    c = [a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi]
    return fits(Range(min(c), max(c)))
