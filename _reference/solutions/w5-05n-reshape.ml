let flatten (shape : int list) (idx : int list) : int =
  List.fold_left2 (fun acc s i -> acc * s + i) 0 shape idx

let unflatten (shape : int list) (f : int) : int list =
  snd (List.fold_right (fun s (rest, out) -> (rest / s, (rest mod s) :: out)) shape (f, []))

let reshape_src (new_shape : int list) (old_shape : int list) (idx : int list) : int list =
  unflatten old_shape (flatten new_shape idx)
