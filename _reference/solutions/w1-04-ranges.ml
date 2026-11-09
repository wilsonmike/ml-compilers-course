type range = { lo : int; hi : int }
let int_min = -2147483648
let int_max = 2147483647
let full = { lo = int_min; hi = int_max }
let fits r = if r.lo < int_min || r.hi > int_max then full else r
let add_range a b = fits { lo = a.lo + b.lo; hi = a.hi + b.hi }
let mul_range a b =
  let c = [a.lo * b.lo; a.lo * b.hi; a.hi * b.lo; a.hi * b.hi] in
  fits { lo = List.fold_left min max_int c; hi = List.fold_left max min_int c }
