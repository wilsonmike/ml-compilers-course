def count(shape: list[int]) -> int:
    n = 1
    for d in shape:
        n = n * d
    return n


def can_reshape(old_shape: list[int], new_shape: list[int]) -> bool:
    return count(old_shape) == count(new_shape)
