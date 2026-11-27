type term =
  | Num of int
  | Param of int
  | Add of term * term
  | Call of term * term list

let rec eval (env : int list) (t : term) : int =
  match t with
  | Num n -> n
  | Param i -> List.nth env i
  | Add (a, b) -> eval env a + eval env b
  | Call (body, args) -> eval (List.map (eval env) args) body
