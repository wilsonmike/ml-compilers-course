def wrap32(x: int) -> int:
    count = x % 2**32
    if count >= 2**31:
        count = count - 2**32
    return count
