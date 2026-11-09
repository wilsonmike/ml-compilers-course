type node = { id : int; op : string; src : node list }

let create () =
  let tbl = Hashtbl.create 64 and next = ref 0 in
  fun op src ->
    let key = (op, List.map (fun n -> n.id) src) in
    match Hashtbl.find_opt tbl key with
    | Some n -> n
    | None -> let n = { id = !next; op; src } in incr next; Hashtbl.add tbl key n; n
