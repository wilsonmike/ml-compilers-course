let alloc_offset (stride : int) (d : int) (i : int) : int =
  if stride = 0 then i
  else
    let e = i - d * stride in
    if e >= 0 && e < stride then e else -1
