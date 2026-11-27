type kind = Load | Store | Op
type node = { name : string; kind : kind; version : string; srcs : string list }

let load name version srcs = { name; kind = Load; version; srcs }
let store name version srcs = { name; kind = Store; version; srcs }
let op name srcs = { name; kind = Op; version = ""; srcs }

let schedule (nodes : node list) : string list =
  let seen = Hashtbl.create 16 in
  let out = ref [] in
  let find name = List.find (fun n -> n.name = name) nodes in
  let needs (n : node) : string list =
    if n.kind = Store then
      n.srcs
      @ List.filter_map
          (fun m -> if m.kind = Load && m.version = n.version then Some m.name else None)
          nodes
    else n.srcs
  in
  let rec visit name =
    if not (Hashtbl.mem seen name) then begin
      Hashtbl.add seen name ();
      List.iter visit (needs (find name));
      out := name :: !out
    end
  in
  List.iter (fun n -> visit n.name) nodes;
  List.rev !out
