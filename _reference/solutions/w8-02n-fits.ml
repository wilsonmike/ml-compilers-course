let fits (c : int) (digits : (int * int) list) : bool =
  let most = List.fold_left (fun acc (d, m) -> acc + d * m) 0 digits in
  c > most
