def alloc_offset(stride: int, d: int, i: int) -> int:
    if stride == 0:
        return i
    e = i - d * stride
    if 0 <= e < stride:
        return e
    return -1
