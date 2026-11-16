def hex32(x: int) -> str:
    return format(x & 0xFFFFFFFF, "08x")
