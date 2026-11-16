type b = T | F | Var of string | Not of b | And of b * b | Or of b * b

let rec to_string e =
  match e with
  | T -> "T"
  | F -> "F"
  | Var s -> s
  | Not a -> "(not " ^ to_string a ^ ")"
  | And (a, b) -> "(" ^ to_string a ^ " and " ^ to_string b ^ ")"
  | Or (a, b) -> "(" ^ to_string a ^ " or " ^ to_string b ^ ")"

let rule e =
  match e with
  | Not T -> Some F
  | Not F -> Some T
  | Not (Not x) -> Some x
  | And (x, T) | And (T, x) -> Some x
  | And (_, F) | And (F, _) -> Some F
  | Or (x, F) | Or (F, x) -> Some x
  | Or (_, T) | Or (T, _) -> Some T
  | _ -> None

let rec simplify e =
  let e =
    match e with
    | Not a -> Not (simplify a)
    | And (a, b) -> And (simplify a, simplify b)
    | Or (a, b) -> Or (simplify a, simplify b)
    | T | F | Var _ -> e
  in
  let rec settle e = match rule e with Some r -> settle r | None -> e in
  settle e
