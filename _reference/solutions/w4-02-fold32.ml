let f32 (x : float) : float = Int32.float_of_bits (Int32.bits_of_float x)

let sum32 (xs : float list) : float =
  match xs with
  | [] -> invalid_arg "sum32: empty"
  | x :: rest -> List.fold_left (fun acc y -> f32 (acc +. y)) x rest
