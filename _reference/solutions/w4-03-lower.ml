type vexp =
  | Vec of string            (* a whole buffer, read as a vector *)
  | Bcast of float           (* expand: the same scalar at every index *)
  | Add of vexp * vexp
  | Mul of vexp * vexp

type sexp =
  | Load of string * string  (* buffer name, index variable: buf[i] *)
  | Const of float
  | SAdd of sexp * sexp
  | SMul of sexp * sexp

let rec show = function
  | Load (b, i) -> b ^ "[" ^ i ^ "]"
  | Const c -> Printf.sprintf "%g" c
  | SAdd (a, b) -> "(" ^ show a ^ " + " ^ show b ^ ")"
  | SMul (a, b) -> "(" ^ show a ^ " * " ^ show b ^ ")"

let rec at (e : vexp) (i : string) : sexp =
  match e with
  | Vec b -> Load (b, i)
  | Bcast c -> Const c
  | Add (a, b) -> SAdd (at a i, at b i)
  | Mul (a, b) -> SMul (at a i, at b i)
