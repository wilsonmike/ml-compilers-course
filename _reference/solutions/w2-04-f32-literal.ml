let c_float (x : float) : string =
  if Float.is_nan x then "NAN"
  else if x = infinity then "INFINITY"
  else if x = neg_infinity then "(-INFINITY)"
  else Printf.sprintf "%h" x ^ "f"
