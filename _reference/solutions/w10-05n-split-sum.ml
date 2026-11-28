let split_sum (xs : float array) (n : int) : float =
  let s = Array.length xs / n in
  let part d =
    let p = ref 0.0 in
    for e = 0 to s - 1 do
      p := !p +. xs.(d * s + e)
    done;
    !p
  in
  let tot = ref (part 0) in
  for d = 1 to n - 1 do
    tot := !tot +. part d
  done;
  !tot
