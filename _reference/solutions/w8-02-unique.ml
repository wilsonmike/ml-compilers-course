(* digits: (coefficient, largest value). True when the offset is a unique mixed-radix number. *)
let unique (digits : (int * int) list) : bool =
  let rec ok = function
    | [] -> true
    | (c, m) :: rest ->
      (m = 0 || c > List.fold_left (fun acc (c2, m2) -> acc + c2 * m2) 0 rest) && ok rest in
  ok (List.sort (fun (a, _) (b, _) -> compare b a) digits)
