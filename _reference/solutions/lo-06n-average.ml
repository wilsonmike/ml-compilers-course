let average (xs : int list) : int =
  match xs with
  | [] -> 0
  | _ -> List.fold_left (fun acc x -> acc + x) 0 xs / List.length xs
