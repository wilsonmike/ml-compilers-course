let coeffs = [1.5252734e-05; 0.0001540353; 0.0013333558; 0.009618129; 0.05550411; 0.2402265; 0.6931472; 1.0]

let small (f : float) : float =
  List.fold_left (fun acc c -> acc *. f +. c) 0.0 coeffs

let pow2 (n : int) : float = Float.ldexp 1.0 n

let exp2 (x : float) : float =
  let n = Float.floor (x +. 0.5) in
  let f = x -. n in
  small f *. pow2 (int_of_float n)
