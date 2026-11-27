from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    name: str

@dataclass(frozen=True)
class Lit:
    value: int

@dataclass(frozen=True)
class Add:
    a: "Node"
    b: "Node"

@dataclass(frozen=True)
class End:
    effect: "Node"
    name: str

Node = Range | Lit | Add | End


def opens(n: Node) -> list[str]:
    match n:
        case Range(name):
            return [name]
        case Lit(_):
            return []
        case Add(a, b):
            return sorted(set(opens(a)) | set(opens(b)))
        case End(effect, name):
            return [x for x in opens(effect) if x != name]
