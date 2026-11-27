let same_f32 (want : float list) (got : float list) : bool =
  List.length want = List.length got
  && List.for_all2
       (fun a b -> (Float.is_nan a && Float.is_nan b) || Int32.bits_of_float a = Int32.bits_of_float b)
       want got
