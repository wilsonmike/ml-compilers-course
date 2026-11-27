from dataclasses import dataclass


@dataclass
class Node:
    op: str
    src: list
    arg: int | None = None


def lit(v):
    return Node("const", [], v)


def square(a):
    return Node("mul", [a, a])


def shared(n):
    return n.src[0] is n.src[1]
