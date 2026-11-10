(* 2^n for -126 <= n <= 127, built from the f32 bit pattern:
   sign 0, exponent field n + 127, mantissa 0. Don't use ** or exp. *)
let pow2 (n : int) : float =
  Int32.float_of_bits (Int32.shift_left (Int32.of_int (n + 127)) 23)
