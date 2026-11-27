def count_lines(lines: list[list]) -> dict[tuple, int]:
    counts = {}
    for line in lines:
        key = tuple(line)
        counts[key] = counts.get(key, 0) + 1
    return counts
