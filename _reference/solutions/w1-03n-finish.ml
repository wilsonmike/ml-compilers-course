type e = Const of int | Var of string | Add of e * e | Mul of e * e

let rec to_string = function
  | Const n -> string_of_int n
  | Var s -> s
  | Add (a, b) -> "(" ^ to_string a ^ " + " ^ to_string b ^ ")"
  | Mul (a, b) -> "(" ^ to_string a ^ " * " ^ to_string b ^ ")"

let wrap32 x = Int32.to_int (Int32.of_int x)

let rule (e : e) : e option =
  match e with
  | Add (Const a, Const b) -> Some (Const (wrap32 (a + b)))
  | Mul (Const a, Const b) -> Some (Const (wrap32 (a * b)))
  | Add (x, Const 0) -> Some x
  | Mul (x, Const 1) -> Some x
  | Add (Add (x, Const a), Const b) -> Some (Add (x, Const (wrap32 (a + b))))
  | _ -> None

let rec again (e : e) : e =
  match rule e with
  | Some r -> again r
  | None -> e

let rec simplify (e : e) : e =
  let e =
    match e with
    | Add (a, b) -> Add (simplify a, simplify b)
    | Mul (a, b) -> Mul (simplify a, simplify b)
    | Const _ | Var _ -> e
  in
  again e
