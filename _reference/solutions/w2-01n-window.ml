let window (data : int list) (off : int) (k : int) : int list =
  if off < 0 || off + k > List.length data then invalid_arg "out of bounds";
  List.filteri (fun i _ -> i >= off && i < off + k) data
