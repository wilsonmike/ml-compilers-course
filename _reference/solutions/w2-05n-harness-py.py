def print_line(slot: int, i: int) -> str:
    return f'printf("{slot} %d\\n", (int)b{slot}[{i}]);'


def harness(bufs: list[tuple[int, list[int]]]) -> list[str]:
    lines = []
    for slot, data in bufs:
        init = ", ".join(str(x) for x in data)
        lines.append(f"static int32_t b{slot}[{len(data)}] = {{{init}}};")
    lines.append("kernel(" + ", ".join(f"b{slot}" for slot, _ in bufs) + ");")
    for slot, data in bufs:
        for i in range(len(data)):
            lines.append(print_line(slot, i))
    return lines
