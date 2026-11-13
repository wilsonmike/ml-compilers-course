def tile_major(row: int, col: int, cols: int) -> int:
    """offset of (row, col) in a matrix of `cols` columns stored as 16x16 tiles, tile after tile"""
    tile = (row // 16) * (cols // 16) + col // 16
    return tile * 256 + (row % 16) * 16 + col % 16
