type vexp =
  | Vec of string
  | Bcast of float
  | Add of vexp * vexp
  | Mul of vexp * vexp

type sexp =
  | Load of string * string
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

let lower_reduce (e : vexp) (n : int) : string =
  Printf.sprintf "acc = %s; for r < %d: acc = acc + %s"
    (show (at e "0")) (n - 1) (show (at e "r+1"))
