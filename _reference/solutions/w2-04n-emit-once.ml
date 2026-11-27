type e = Lit of int | Var of string | Add of e * e | Mul of e * e

let emit (e : e) : string list * string =
  let lines = ref [] in
  let names : (e * string) list ref = ref [] in
  let rec go e =
    match e with
    | Lit n -> string_of_int n
    | Var s -> s
    | Add (a, b) | Mul (a, b) ->
      (match List.assq_opt e !names with
       | Some v -> v
       | None ->
        let x = go a in
        let y = go b in
        let op = match e with Add _ -> "+" | _ -> "*" in
        let v = Printf.sprintf "v%d" (List.length !lines) in
        lines := Printf.sprintf "int32_t %s = (int32_t)((uint32_t)%s %s (uint32_t)%s);" v x op y :: !lines;
        names := (e, v) :: !names;
        v)
  in
  let result = go e in
  ignore names;
  (List.rev !lines, result)
