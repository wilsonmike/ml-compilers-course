let offset (shape : int list) (index : int list) : int =
  let rec go shape index stride =
    match shape, index with
    | size :: shape', i :: index' -> i * stride + go shape' index' (stride * size)
    | _ -> 0
  in
  go (List.rev shape) (List.rev index) 1
