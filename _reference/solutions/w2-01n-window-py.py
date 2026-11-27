def window(data: list[int], off: int, k: int) -> list[int]:
    if off < 0 or off + k > len(data):
        raise ValueError("out of bounds")
    return data[off:off + k]
