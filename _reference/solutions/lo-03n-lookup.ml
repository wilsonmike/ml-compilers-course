let rec lookup name items =
  match items with
  | [] -> None
  | (n, p) :: rest -> if n = name then Some p else lookup name rest
