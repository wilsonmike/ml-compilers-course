let owns (s : int) (t : int) (off : int) (size : int) : bool =
  off >= t * s && off + size <= (t + 1) * s
