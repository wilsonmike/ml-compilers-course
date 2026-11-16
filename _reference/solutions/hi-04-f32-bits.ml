let f32_bits (x : float) : int = Int32.to_int (Int32.bits_of_float x) land 0xFFFFFFFF
