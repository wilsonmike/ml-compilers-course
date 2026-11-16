from dataclasses import dataclass


@dataclass(frozen=True)
class Num:
    n: int


@dataclass(frozen=True)
class Add:
    a: "Num | Add"
    b: "Num | Add"


def chain(k: int) -> "Num | Add":
    s = Num(1)
    for _ in range(k):
        s = Add(s, s)
    return s


def tree_size(e: "Num | Add") -> int:
    memo: dict[int, int] = {}

    def go(e) -> int:
        key = id(e)
        if key in memo:
            return memo[key]
        match e:
            case Num():
                n = 1
            case Add(a, b):
                n = 1 + go(a) + go(b)
        memo[key] = n
        return n

    return go(e)
