type node = { id : int; op : string; src : node list }

let make (tbl : (string, node) Hashtbl.t) (next : int ref) (op : string) : node =
  match Hashtbl.find_opt tbl op with
  | Some n -> n
  | None ->
    let n = { id = !next; op = op; src = [] } in
    incr next;
    Hashtbl.replace tbl op n;
    n
