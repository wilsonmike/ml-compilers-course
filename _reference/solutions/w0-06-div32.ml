let div32 (a : int) (b : int) : int =
  if b = 0 then -1
  else
    let q = a / b in
    let q = if a mod b <> 0 && (a < 0) <> (b < 0) then q - 1 else q in
    Int32.to_int (Int32.of_int q)
