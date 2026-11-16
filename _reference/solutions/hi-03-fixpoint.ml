let fixpoint (f : 'a -> 'a) (x : 'a) : 'a * int =
  let rec go x count =
    let y = f x in
    if y = x then (x, count) else go y (count + 1)
  in
  go x 0
