let permute_shape (shape : int list) (order : int list) : int list =
  List.map (fun p -> List.nth shape p) order

let src_index (order : int list) (idx : int list) : int list =
  let n = List.length order in
  List.init n (fun a ->
    let rec find k = function
      | [] -> failwith "not a permutation"
      | p :: rest -> if p = a then List.nth idx k else find (k + 1) rest
    in
    find 0 order)
