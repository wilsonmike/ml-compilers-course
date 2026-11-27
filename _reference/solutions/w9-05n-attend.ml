let attend (pairs : (float * float) list) : float =
  let (_, l, acc) = List.fold_left (fun (m, l, acc) (s, v) ->
    let m' = Float.max m s in
    let c = exp (m -. m') in
    let p = exp (s -. m') in
    (m', l *. c +. p, acc *. c +. p *. v)) (neg_infinity, 0.0, 0.0) pairs in
  acc /. l
