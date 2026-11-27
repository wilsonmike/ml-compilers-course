let slice_ok (s : int) (terms : (int * int) list) (size : int) : bool =
  let lo = List.fold_left (fun a (l, _) -> a + l) 0 terms in
  let hi = List.fold_left (fun a (_, h) -> a + h) 0 terms in
  lo >= 0 && hi + size <= s
