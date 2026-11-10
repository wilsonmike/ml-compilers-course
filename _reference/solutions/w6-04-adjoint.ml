(* The order that undoes permute order=... *)
let inverse_order (order : int list) : int list =
  let inv = Array.make (List.length order) 0 in
  List.iteri (fun k p -> inv.(p) <- k) order;
  Array.to_list inv

(* The axes that expand x_shape -> out_shape grew: its gradient sums over them. *)
let summed_axes (x_shape : int list) (out_shape : int list) : int list =
  List.concat (List.mapi (fun k (a, b) -> if a = 1 && b <> 1 then [k] else []) (List.combine x_shape out_shape))
