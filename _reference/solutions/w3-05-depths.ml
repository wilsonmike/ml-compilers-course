type node =
  | Range of int * string      (* nesting depth (1 = outermost) and name *)
  | Op of string * node list

let rec depth (n : node) : int =
  match n with
  | Range (d, _) -> d
  | Op (_, srcs) -> List.fold_left (fun acc s -> max acc (depth s)) 0 srcs
