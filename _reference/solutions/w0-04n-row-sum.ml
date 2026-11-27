let row_sum (grid : int list) (cols : int) (r : int) : int =
  let rec go c = if c = cols then 0 else List.nth grid (r * cols + c) + go (c + 1) in
  go 0
