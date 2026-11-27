let apply (op : string) (a : int) (b : int) : int =
  match op with
  | "add" -> a + b
  | "mul" -> a * b
  | "max" -> max a b
  | _ -> failwith op
