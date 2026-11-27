type node = { id : int; op : string; src : node list }

let label (n : node) : string =
  string_of_int n.id ^ ": " ^ n.op ^ " (" ^ string_of_int (List.length n.src) ^ ")"
