def buffer_bytes(devices: int, size: int, elem: int, written: bool, stride: int) -> int:
    if stride == 0:
        return devices * size * elem
    moved = devices * stride * elem
    if written:
        moved = moved + devices * stride * elem
    return moved
