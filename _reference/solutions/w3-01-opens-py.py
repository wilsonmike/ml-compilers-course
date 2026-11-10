from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    name: str   # a named loop counter
    bound: int  # and its bound

@dataclass(frozen=True)
class Const:
    value: int

@dataclass(frozen=True)
class Add:
    a: "Node"
    b: "Node"

@dataclass(frozen=True)
class Store:
    offset: "Node"
    value: "Node"

@dataclass(frozen=True)
class End:
    effect: "Node"
    range: "Node"  # closes this range

Node = Range | Const | Add | Store | End


def opens(n: Node) -> list[str]:
    match n:
        case Range(name, _):
            return [name]
        case Const(_):
            return []
        case Add(a, b) | Store(a, b):
            return sorted(set(opens(a)) | set(opens(b)))
        case End(e, Range(name, _)):
            return [x for x in opens(e) if x != name]
        case End(e, _):
            return opens(e)
