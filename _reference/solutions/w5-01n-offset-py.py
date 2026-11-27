def offset(shape, index):
    off = 0
    stride = 1
    for axis in reversed(range(len(shape))):
        off = off + index[axis] * stride
        stride = stride * shape[axis]
    return off
