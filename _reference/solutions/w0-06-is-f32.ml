let is_f32 (x : float) : bool =
  Float.is_nan x || Int32.float_of_bits (Int32.bits_of_float x) = x
