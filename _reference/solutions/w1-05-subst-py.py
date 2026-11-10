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


def show(t: Term) -> str:
    """Given: prints a term. Keep it. The tests use it."""
    match t:
        case Num(n):
            return str(n)
        case Param(i):
            return f"p{i}"
        case Add(a, b):
            return f"add({show(a)}, {show(b)})"
        case Call(body, args):
            return f"call({show(body)}, [{'; '.join(show(x) for x in args)}])"


def subst(args: list[Term], t: Term) -> Term:
    match t:
        case Param(i) if 0 <= i < len(args):
            return args[i]
        case Add(a, b):
            return Add(subst(args, a), subst(args, b))
        case Call(body, xs):
            return Call(body, [subst(args, x) for x in xs])  # the body is closed: keep it as is
        case _:
            return t
