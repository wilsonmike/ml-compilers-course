let dot (a : int array) (b : int array) : int =
  let total = ref 0 in
  for k = 0 to Array.length a - 1 do
    total := !total + a.(k) * b.(k)
  done;
  !total
