let rec sum_from acc l =
  match l with
  | [] -> acc
  | x :: rest -> sum_from (acc + x) rest
