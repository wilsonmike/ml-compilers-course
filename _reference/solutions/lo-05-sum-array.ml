let sum (a : int array) : int =
  let total = ref 0 in
  for i = 0 to Array.length a - 1 do
    total := !total + a.(i)
  done;
  !total
