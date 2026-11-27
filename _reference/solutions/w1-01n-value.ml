type node = { op : string; src : node list; arg : int option }

let lit v = { op = "const"; src = []; arg = Some v }
let node op a b = { op; src = [a; b]; arg = None }

let rec value (n : node) : int =
  match n.op, n.src, n.arg with
  | "const", [], Some v -> v
  | "add", [a; b], None -> value a + value b
  | "mul", [a; b], None -> value a * value b
  | _ -> failwith "not a node this toy knows"
