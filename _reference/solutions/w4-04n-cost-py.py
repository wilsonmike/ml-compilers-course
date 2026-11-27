def fuse_cost(ops, uses, n):
    return ops * uses * n


def stage_cost(ops, uses, n, mem):
    return ops * n + mem * n + mem * uses * n


def choose(ops, uses, n, mem):
    if stage_cost(ops, uses, n, mem) < fuse_cost(ops, uses, n):
        return "stage"
    return "fuse"
