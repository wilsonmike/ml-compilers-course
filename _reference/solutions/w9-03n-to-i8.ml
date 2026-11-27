let to_i8 (x : int) : int =
  ((x + 128) land 255) - 128
