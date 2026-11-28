let smallest_work (n : int) (copy : int) : int =
  let rec go w = if w + n * copy < n * w then w else go (w + 1) in
  go 1
