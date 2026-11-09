let f32 (x : float) : float = Int32.float_of_bits (Int32.bits_of_float x)

let add32 (a : float) (b : float) : float = f32 (a +. b)
