type node =
  | Range of string * int
  | Const of int
  | Add of node * node
  | Store of node * node
  | End of node * node

let rec opens (n : node) : string list =
  match n with
  | Range (s, _) -> [s]
  | Const _ -> []
  | Add (a, b) | Store (a, b) -> List.sort_uniq compare (opens a @ opens b)
  | End (e, r) ->
    let gone = (match r with Range (s, _) -> s | _ -> "") in
    List.filter (fun x -> x <> gone) (opens e)
