type t = Leaf of int | Add of t * t

(* n doublings: one Leaf and n Adds, each Add using the node below it twice. *)
let rec dbl n = if n = 0 then Leaf 1 else let s = dbl (n - 1) in Add (s, s)

let dag_size t =
  let seen = ref [] in
  let rec go t =
    if not (List.memq t !seen) then begin
      seen := t :: !seen;
      match t with Leaf _ -> () | Add (a, b) -> go a; go b
    end in
  go t; List.length !seen
