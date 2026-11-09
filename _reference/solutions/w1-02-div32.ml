let div32 (a : int) (b : int) : int option =
  if b = 0 then None else Some (Int32.to_int (Int32.of_int (a / b)))
