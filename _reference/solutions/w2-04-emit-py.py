from dataclasses import dataclass


@dataclass(frozen=True)
class Lit:
    n: int


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Add:
    a: "E"
    b: "E"


@dataclass(frozen=True)
class Mul:
    a: "E"
    b: "E"


E = Lit | Var | Add | Mul


def emit(e: E) -> tuple[list[str], str]:
    lines: list[str] = []
    names: dict[int, str] = {}  # id(node) -> its C name. Every node stays alive inside e.

    def go(e: E) -> str:
        match e:
            case Lit(n):
                return "(-2147483647 - 1)" if n == -(2**31) else str(n)
            case Var(s):
                return s
            case Add(a, b) | Mul(a, b):
                if id(e) in names:
                    return names[id(e)]
                x, y = go(a), go(b)
                op = "+" if isinstance(e, Add) else "*"
                v = f"v{len(lines)}"
                lines.append(f"int32_t {v} = (int32_t)((uint32_t){x} {op} (uint32_t){y});")
                names[id(e)] = v
                return v

    r = go(e)
    return lines, r
