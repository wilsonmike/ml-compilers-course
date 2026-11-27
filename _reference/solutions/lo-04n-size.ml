type expr = Num of int | Add of expr * expr | Mul of expr * expr

let rec size (e : expr) : int =
  match e with
  | Num _ -> 1
  | Add (a, b) -> 1 + size a + size b
  | Mul (a, b) -> 1 + size a + size b
