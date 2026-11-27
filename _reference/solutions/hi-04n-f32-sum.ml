let to_f32 (x : float) : float = Int32.float_of_bits (Int32.bits_of_float x)

let sum3 (a : float) (b : float) (c : float) : float =
  to_f32 (to_f32 (a +. b) +. c)
