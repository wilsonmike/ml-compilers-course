let first_or default l =
  match l with
  | [] -> default
  | x :: _ -> x
