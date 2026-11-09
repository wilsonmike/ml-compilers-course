type e = Lit of int | Var of string | Add of e * e | Mul of e * e

let emit (e : e) : string list * string =
  let lines = ref [] and count = ref 0 and seen = ref [] in
  let lit k = if k = -2147483648 then "(-2147483647 - 1)" else string_of_int k in
  let rec go e =
    match e with
    | Lit k -> lit k
    | Var s -> s
    | Add (a, b) | Mul (a, b) ->
      (match List.assq_opt e !seen with
       | Some v -> v
       | None ->
         let x = go a in
         let y = go b in
         let op = match e with Add _ -> "+" | _ -> "*" in
         let v = Printf.sprintf "v%d" !count in
         incr count;
         lines := Printf.sprintf "int32_t %s = (int32_t)((uint32_t)%s %s (uint32_t)%s);" v x op y :: !lines;
         seen := (e, v) :: !seen;
         v)
  in
  let r = go e in
  (List.rev !lines, r)
