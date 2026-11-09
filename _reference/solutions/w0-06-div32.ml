let div32 (a : int) (b : int) : int =
  Int32.to_int (Int32.div (Int32.of_int a) (Int32.of_int b))
