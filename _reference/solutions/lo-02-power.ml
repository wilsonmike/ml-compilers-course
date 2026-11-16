let rec power base exp =
  if exp = 0 then 1 else base * power base (exp - 1)
