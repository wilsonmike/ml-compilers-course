let tile_bytes (n : int) (bm : int) : int =
  let blocks = (n / bm) * (n / bm) in
  let floats_per_block = 2 * bm * n in
  blocks * floats_per_block * 4
