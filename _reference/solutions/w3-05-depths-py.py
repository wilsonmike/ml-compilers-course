from dataclasses import dataclass


@dataclass
class Range:
    depth: int  # nesting depth, 1 = outermost
    name: str

@dataclass
class Op:
    name: str
    srcs: list["Node"]

Node = Range | Op


def depth(n: Node) -> int:
    match n:
        case Range(d, _):
            return d
        case Op(_, srcs):
            return max((depth(s) for s in srcs), default=0)
