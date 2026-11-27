type e =
  | Lit of float
  | Var of string
  | Add of e * e
  | Mul of e * e
  | Exp2 of e
  | Log2 of e
  | Sub of e * e
  | Exp of e
  | Log of e

let rec to_string = function
  | Lit x -> Printf.sprintf "%.7g" x
  | Var s -> s
  | Add (a, b) -> "(add " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Mul (a, b) -> "(mul " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Exp2 a -> "(exp2 " ^ to_string a ^ ")"
  | Log2 a -> "(log2 " ^ to_string a ^ ")"
  | Sub (a, b) -> "(sub " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Exp a -> "(exp " ^ to_string a ^ ")"
  | Log a -> "(log " ^ to_string a ^ ")"

let rec desugar (e : e) : e =
  match e with
  | Lit _ | Var _ -> e
  | Add (a, b) -> Add (desugar a, desugar b)
  | Mul (a, b) -> Mul (desugar a, desugar b)
  | Exp2 a -> Exp2 (desugar a)
  | Log2 a -> Log2 (desugar a)
  | Sub (a, b) -> Add (desugar a, Mul (desugar b, Lit (-1.0)))
  | Exp a -> Exp2 (Mul (desugar a, Lit 1.442695))
  | Log a -> Mul (Log2 (desugar a), Lit 0.6931472)
