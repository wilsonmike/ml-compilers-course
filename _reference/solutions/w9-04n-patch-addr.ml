let patch_addr (row : int) (col : int) (w : int) : int =
  let y = row / w and x = row mod w in
  let dy = col / 3 and dx = col mod 3 in
  (y + dy) * (w + 2) + x + dx
