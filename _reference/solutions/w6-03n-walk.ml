type node = X of float | Const of float | Add of int * int | Mul of int * int

let backward (tape : node list) (value : float list) : float list =
  let t = Array.of_list tape in
  let v = Array.of_list value in
  let n = Array.length t in
  let g = Array.make n 0.0 in
  g.(n - 1) <- 1.0;
  for i = n - 1 downto 0 do
    match t.(i) with
    | Add (a, b) ->
      g.(a) <- g.(a) +. g.(i);
      g.(b) <- g.(b) +. g.(i)
    | Mul (a, b) ->
      g.(a) <- g.(a) +. g.(i) *. v.(b);
      g.(b) <- g.(b) +. g.(i) *. v.(a)
    | X _ | Const _ -> ()
  done;
  Array.to_list g
