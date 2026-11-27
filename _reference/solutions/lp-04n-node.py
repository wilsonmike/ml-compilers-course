from dataclasses import dataclass


@dataclass
class Node:
    op: str
    src: list
    arg: int | None = None


def lit(v):
    return Node("const", [], v)
