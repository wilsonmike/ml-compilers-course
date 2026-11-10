from collections import Counter


def stage_set(g: list[tuple[int, list[int]]]) -> list[int]:
    uses = Counter(s for _, srcs in g for s in set(srcs))
    return sorted(i for i, srcs in g if srcs and uses[i] >= 2)
