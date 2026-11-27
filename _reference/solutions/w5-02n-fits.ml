let count (shape : int list) : int =
  List.fold_left (fun n d -> n * d) 1 shape

let can_reshape (old_shape : int list) (new_shape : int list) : bool =
  count old_shape = count new_shape
