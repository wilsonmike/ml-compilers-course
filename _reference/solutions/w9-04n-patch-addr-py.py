def patch_addr(row: int, col: int, w: int) -> int:
    y, x = row // w, row % w
    dy, dx = col // 3, col % 3
    return (y + dy) * (w + 2) + x + dx
