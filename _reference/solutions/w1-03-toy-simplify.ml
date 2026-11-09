type e = Const of int | Var of string | Add of e * e | Mul of e * e

(* Used to print test results. Don't change it. *)
let rec to_string = function
  | Const n -> string_of_int n
  | Var s -> s
  | Add (a, b) -> "(" ^ to_string a ^ " + " ^ to_string b ^ ")"
  | Mul (a, b) -> "(" ^ to_string a ^ " * " ^ to_string b ^ ")"

let wrap32 x = Int32.to_int (Int32.of_int x)

let rule = function
  | Add (Const a, Const b) -> Some (Const (wrap32 (a + b)))
  | Mul (Const a, Const b) -> Some (Const (wrap32 (a * b)))
  | Add (Const c, x) -> Some (Add (x, Const c))
  | Mul (Const c, x) -> Some (Mul (x, Const c))
  | Add (x, Const 0) -> Some x
  | Mul (x, Const 1) -> Some x
  | Mul (_, Const 0) -> Some (Const 0)
  | Add (Add (x, Const a), Const b) -> Some (Add (x, Const (wrap32 (a + b))))
  | Mul (Mul (x, Const a), Const b) -> Some (Mul (x, Const (wrap32 (a * b))))
  | _ -> None

let rec fix e = match rule e with Some e' -> fix e' | None -> e

let rec simplify e = match e with
  | Add (a, b) -> fix (Add (simplify a, simplify b))
  | Mul (a, b) -> fix (Mul (simplify a, simplify b))
  | e -> e
