let divs (a : int) (b : int) : int * int * int * int =
  let q = a / b and r = a mod b in
  if r <> 0 && (r < 0) <> (b < 0) then (q, r, q - 1, r + b) else (q, r, q, r)
