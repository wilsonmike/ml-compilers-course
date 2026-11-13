(* offset of (row, col) in a matrix of cols columns stored as 16x16 tiles, tile after tile *)
let tile_major (row : int) (col : int) (cols : int) : int =
  let tile = (row / 16) * (cols / 16) + col / 16 in
  tile * 256 + (row mod 16) * 16 + col mod 16
