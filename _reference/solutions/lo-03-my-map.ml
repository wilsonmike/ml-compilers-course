let rec my_map f l =
  match l with
  | [] -> []
  | x :: rest -> f x :: my_map f rest
