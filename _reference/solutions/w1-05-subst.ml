type term =
  | Num of int
  | Param of int
  | Add of term * term
  | Call of term * term list   (* Call (body, args) *)

(* Given: prints a term. Keep it; the tests use it. *)
let rec show = function
  | Num n -> string_of_int n
  | Param i -> "p" ^ string_of_int i
  | Add (a, b) -> "add(" ^ show a ^ ", " ^ show b ^ ")"
  | Call (f, args) -> "call(" ^ show f ^ ", [" ^ String.concat "; " (List.map show args) ^ "])"

let rec subst args t = match t with
  | Num _ -> t
  | Param i -> (match List.nth_opt args i with Some a -> a | None -> t)
  | Add (a, b) -> Add (subst args a, subst args b)
  | Call (f, xs) -> Call (f, List.map (subst args) xs)
