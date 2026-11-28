let place (n : int) (size : int) (accesses : (bool * int * int * int) list) : int =
  let s = match accesses with (_, s, _, _) :: _ -> s | [] -> 0 in
  let ok (_, s', lo, hi) = s' = s && s >= 1 && lo >= 0 && hi + 1 <= s in
  if List.for_all ok accesses && n * s <= size then s
  else if List.exists (fun (w, _, _, _) -> w) accesses then -1
  else 0
