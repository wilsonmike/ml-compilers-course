type node = X of float | Const of float | Add of int * int | Mul of int * int

(* d(last entry)/d(entry i) for every i. Add and Mul index earlier entries. *)
let grads (tape : node list) : float list =
  let t = Array.of_list tape in
  let n = Array.length t in
  let v = Array.make n 0.0 in
  Array.iteri (fun i node ->                            (* forward: every value, in order *)
    v.(i) <- (match node with
      | X x | Const x -> x
      | Add (a, b) -> v.(a) +. v.(b)
      | Mul (a, b) -> v.(a) *. v.(b))) t;
  let g = Array.make n 0.0 in
  g.(n - 1) <- 1.0;                                     (* the seed *)
  for i = n - 1 downto 0 do                             (* backward *)
    match t.(i) with
    | Add (a, b) -> g.(a) <- g.(a) +. g.(i); g.(b) <- g.(b) +. g.(i)
    | Mul (a, b) -> g.(a) <- g.(a) +. g.(i) *. v.(b); g.(b) <- g.(b) +. g.(i) *. v.(a)
    | X _ | Const _ -> ()
  done;
  Array.to_list g
