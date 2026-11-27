from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    lo: int
    hi: int


def const_range(v: int) -> Range:
    return Range(v, v)


def max_range(a: Range, b: Range) -> Range:
    return Range(max(a.lo, b.lo), max(a.hi, b.hi))


def cmplt_range(a: Range, b: Range) -> Range:
    if a.hi < b.lo:
        return Range(1, 1)
    if a.lo >= b.hi:
        return Range(0, 0)
    return Range(0, 1)
