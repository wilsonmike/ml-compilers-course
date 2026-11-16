type e = Num of int | Add of e * e

let rec chain k = if k = 0 then Num 1 else let s = chain (k - 1) in Add (s, s)

let tree_size (e : e) : int =
  let memo = ref [] in
  let rec go e =
    match List.assq_opt e !memo with
    | Some n -> n
    | None ->
      let n = match e with Num _ -> 1 | Add (a, b) -> 1 + go a + go b in
      memo := (e, n) :: !memo;
      n
  in
  go e
