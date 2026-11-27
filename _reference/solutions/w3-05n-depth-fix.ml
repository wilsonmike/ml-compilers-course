let depth_in (order : string list) (opens : string list) : int =
  let rec go d best = function
    | [] -> best
    | r :: rest -> go (d + 1) (if List.mem r opens then d else best) rest
  in
  go 1 0 order
