type e = Const of int | Var of string | Add of e * e | Mul of e * e

let rec show e =
  match e with
  | Const n -> string_of_int n
  | Var s -> s
  | Add (a, b) -> "(" ^ show a ^ " + " ^ show b ^ ")"
  | Mul (a, b) -> "(" ^ show a ^ " * " ^ show b ^ ")"

let rule e =
  match e with
  | Add (x, Const 0) -> Some x
  | Mul (x, Const 1) -> Some x
  | Add (Const m, Const n) -> Some (Const (m + n))
  | Mul (Const m, Const n) -> Some (Const (m * n))
  | _ -> None
