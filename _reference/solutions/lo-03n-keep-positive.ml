let rec keep_positive l =
  match l with
  | [] -> []
  | x :: rest -> if x > 0 then x :: keep_positive rest else keep_positive rest
