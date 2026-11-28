let buffer_bytes (devices : int) (size : int) (elem : int) (written : bool) (stride : int) : int =
  if stride = 0 then devices * size * elem
  else begin
    let moved = ref (devices * stride * elem) in
    if written then moved := !moved + devices * stride * elem;
    !moved
  end
