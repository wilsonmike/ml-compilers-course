let result_dtype (op : string) (a : string) (b : string) : string =
  match op with
  | "add" | "mul" | "max" | "xor" -> if a = b then a else "rejected"
  | "cmplt" -> if a = b then "bool" else "rejected"
  | "div" | "mod" | "shl" -> if a = "i32" && b = "i32" then "i32" else "rejected"
  | _ -> "rejected"
