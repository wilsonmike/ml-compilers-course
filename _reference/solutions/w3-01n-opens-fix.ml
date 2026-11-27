type node =
  | Range of string
  | Lit of int
  | Add of node * node
  | End of node * string

let rec opens (n : node) : string list =
  match n with
  | Range name -> [name]
  | Lit _ -> []
  | Add (a, b) -> List.sort_uniq compare (opens a @ opens b)
  | End (e, name) -> List.filter (fun x -> x <> name) (opens e)
