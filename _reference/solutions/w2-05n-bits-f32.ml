let bits_to_f32 (bits : string) : float =
  let n = Int32.of_string ("0x" ^ bits) in
  Int32.float_of_bits n
