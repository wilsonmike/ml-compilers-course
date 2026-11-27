from dataclasses import dataclass


@dataclass(frozen=True)
class Num:
    n: int


@dataclass(frozen=True)
class Param:
    i: int


@dataclass(frozen=True)
class Add:
    a: "Term"
    b: "Term"


@dataclass(frozen=True)
class Call:
    body: "Term"
    args: list["Term"]


Term = Num | Param | Add | Call


def ev(env: list[int], t: Term) -> int:
    match t:
        case Num(n):
            return n
        case Param(i):
            return env[i]
        case Add(a, b):
            return ev(env, a) + ev(env, b)
        case Call(body, args):
            return ev([ev(env, x) for x in args], body)
