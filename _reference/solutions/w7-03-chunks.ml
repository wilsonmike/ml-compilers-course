(* One contiguous (lo, hi) range per thread, for n iterations on t threads. *)
let chunks (n : int) (t : int) : (int * int) list =
  let m = max 1 (min t n) in
  List.init m (fun k -> (n * k / m, n * (k + 1) / m))
