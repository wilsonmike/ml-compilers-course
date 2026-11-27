def row_sum(grid, cols, r):
    total = 0
    for c in range(cols):
        total = total + grid[r * cols + c]
    return total
