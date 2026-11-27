let wrap32 x = Int32.to_int (Int32.of_int x)

let prod32 (xs : int list) : int =
  match xs with
  | [] -> 0
  | x :: rest -> List.fold_left (fun acc y -> wrap32 (acc * y)) x rest
