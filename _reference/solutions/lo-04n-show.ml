type arg = Lit of int | Name of string

let show (a : arg) : string =
  match a with
  | Lit n -> string_of_int n
  | Name s -> "%" ^ s
