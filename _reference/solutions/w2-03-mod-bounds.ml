let fdiv a b = if a mod b <> 0 && (a < 0) <> (b < 0) then a / b - 1 else a / b

let mod_bounds ((lo, hi) : int * int) (y : int) : int * int =
  if y = 0 then (lo, hi)
  else if fdiv lo y = fdiv hi y then
    let a = lo - y * fdiv lo y and b = hi - y * fdiv hi y in
    (min a b, max a b)
  else if y > 0 then (0, y - 1)
  else (y + 1, 0)
