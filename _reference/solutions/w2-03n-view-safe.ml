let view_safe ((lo, hi) : int * int) (n : int) (k : int) : bool =
  let last_start = n - k in
  lo >= 0 && hi <= last_start
