(* the running max m and sum l of exp(s - m), in one pass over the scores *)
let online (scores : float list) : float * float =
  List.fold_left (fun (m, l) s ->
    let m' = Float.max m s in
    (m', l *. exp (m -. m') +. exp (s -. m'))) (neg_infinity, 0.0) scores
