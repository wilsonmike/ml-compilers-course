let rec pad_shape (shape : int list) (pads : int list) : int list =
  match shape, pads with
  | d :: s, l :: r :: p -> (d + l + r) :: pad_shape s p
  | _ -> []

let expand_src (shape : int list) (idx : int list) : int list =
  List.map2 (fun d i -> if d = 1 then 0 else i) shape idx
