let horner (coeffs : float list) (x : float) : float =
  List.fold_left (fun acc c -> acc *. x +. c) 0.0 coeffs
