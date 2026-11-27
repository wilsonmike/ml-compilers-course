let coat_check (slips : (string * string) list) : int list =
  let notebook = Hashtbl.create 16 in
  List.map
    (fun (color, size) ->
      let slip = (color, size) in
      match Hashtbl.find_opt notebook slip with
      | Some ticket -> ticket
      | None ->
        let ticket = Hashtbl.length notebook in
        Hashtbl.add notebook slip ticket;
        ticket)
    slips
