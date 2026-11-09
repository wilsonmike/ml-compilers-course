let mod_bounds ((lo, hi) : int * int) (m : int) : int * int =
  if lo >= 0 then (0, min (m - 1) hi)
  else if hi < 0 then (max (-(m - 1)) lo, 0)
  else (max (-(m - 1)) lo, min (m - 1) hi)
