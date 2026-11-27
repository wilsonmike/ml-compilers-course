from dataclasses import dataclass


@dataclass(frozen=True)
class Lit:
    n: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Add:
    a: object
    b: object


@dataclass(frozen=True)
class Mul:
    a: object
    b: object


def emit(e):
    lines = []
    names = {}

    def go(e):
        if isinstance(e, Lit):
            return str(e.n)
        if isinstance(e, Var):
            return e.name
        if id(e) in names:
            return names[id(e)]
        a = go(e.a)
        b = go(e.b)
        op = "+" if isinstance(e, Add) else "*"
        v = f"v{len(lines)}"
        lines.append(f"int32_t {v} = (int32_t)((uint32_t){a} {op} (uint32_t){b});")
        names[id(e)] = v
        return v

    result = go(e)
    return lines, result
