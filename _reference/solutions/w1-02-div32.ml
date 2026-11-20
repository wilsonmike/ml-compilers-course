let divmod32 (a : int) (b : int) : int * int =
  if b = 0 then (-1, a)
  else
    let q = a / b in
    let q = if a mod b <> 0 && (a < 0) <> (b < 0) then q - 1 else q in
    let wrap x = Int32.to_int (Int32.of_int x) in
    (wrap q, wrap (a - b * q))
