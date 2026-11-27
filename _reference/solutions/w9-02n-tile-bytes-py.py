def tile_bytes(n: int, bm: int) -> int:
    blocks = (n // bm) * (n // bm)
    floats_per_block = 2 * bm * n
    return blocks * floats_per_block * 4
