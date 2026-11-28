let loop_bytes (devices : int) (bufs : (int * int * bool * int) list) : int =
  List.fold_left (fun acc (size, elem, written, stride) ->
      if stride = 0 then acc + devices * size * elem
      else acc + devices * stride * elem * (if written then 2 else 1))
    0 bufs
