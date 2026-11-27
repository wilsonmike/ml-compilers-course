def owns(s: int, t: int, off: int, size: int) -> bool:
    return off >= t * s and off + size <= (t + 1) * s
