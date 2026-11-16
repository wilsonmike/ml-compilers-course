let count_positive l =
  List.fold_left (fun acc x -> if x > 0 then acc + 1 else acc) 0 l
