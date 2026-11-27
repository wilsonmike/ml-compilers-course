type e =
  | Lit of float
  | Var of string
  | Add of e * e
  | Mul of e * e
  | Max of e * e
  | Recip of e
  | Neg of e
  | Sub of e * e
  | Relu of e
  | Fdiv of e * e

let rec to_string = function
  | Lit x -> Printf.sprintf "%.7g" x
  | Var s -> s
  | Add (a, b) -> "(add " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Mul (a, b) -> "(mul " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Max (a, b) -> "(max " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Recip a -> "(recip " ^ to_string a ^ ")"
  | Neg a -> "(neg " ^ to_string a ^ ")"
  | Sub (a, b) -> "(sub " ^ to_string a ^ " " ^ to_string b ^ ")"
  | Relu a -> "(relu " ^ to_string a ^ ")"
  | Fdiv (a, b) -> "(fdiv " ^ to_string a ^ " " ^ to_string b ^ ")"

let rec desugar (e : e) : e =
  match e with
  | Lit _ | Var _ -> e
  | Add (a, b) -> Add (desugar a, desugar b)
  | Mul (a, b) -> Mul (desugar a, desugar b)
  | Max (a, b) -> Max (desugar a, desugar b)
  | Recip a -> Recip (desugar a)
  | Neg a -> Mul (desugar a, Lit (-1.0))
  | Sub (a, b) -> Add (desugar a, desugar (Neg b))
  | Relu a -> Max (desugar a, Lit 0.0)
  | Fdiv (a, b) -> Mul (desugar a, Recip (desugar b))
